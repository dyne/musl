"""Pinned Git inputs and compiler-cache behavior, including real cache hits."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import unittest

from test_build import ROOT, Workspace, run


class GitSources(Workspace):
    def setUp(self):
        super().setUp()
        self.repo = self.work / "upstream.git"
        self.ok(run("git", "init", "-q", str(self.repo)))
        self.payload = b"pinned helper bytes\n"
        (self.repo / "helper").write_bytes(self.payload)
        self.commit()
        self.revision = self.ok(run("git", "rev-parse", "HEAD", cwd=self.repo)).stdout.strip()
        # The current branch changes; fetch must still select the pinned object.
        (self.repo / "helper").write_text("newer, unselected helper\n")
        self.commit()
        self.dest = self.work / "source cache/config.sub"
        self.manifest = self.work / "sources.sha256"
        self.manifest.write_text(hashlib.sha256(self.payload).hexdigest() + "  config.sub\n")

    def commit(self):
        self.ok(run("git", "add", "helper", cwd=self.repo))
        self.ok(run("git", "-c", "user.name=Fixture", "-c", "user.email=test@example.org",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "helper", cwd=self.repo))

    def download(self, revision=None, path="helper", env=None):
        url = f"git+{self.repo.as_uri()}#{revision or self.revision}:{path}"
        return run("sh", str(ROOT / "scripts/download.sh"), url, str(self.dest),
                   str(self.manifest), env=env)

    def test_pinned_git_blob_and_offline_cached_reuse(self):
        self.ok(self.download())
        self.assertEqual(self.dest.read_bytes(), self.payload)
        before = self.dest.stat().st_mtime_ns
        shutil.rmtree(self.repo)
        self.ok(self.download())
        self.assertEqual(self.dest.stat().st_mtime_ns, before)
        self.assertEqual(list(self.dest.parent.glob("*.git.*")), [])

    def test_git_requires_full_commit_and_existing_blob_and_matching_digest(self):
        for revision, path in [(self.revision[:12], "helper"), (self.revision, "missing"),
                               (self.revision, "../helper")]:
            self.assertNotEqual(self.download(revision, path).returncode, 0)
            self.assertFalse(self.dest.exists())
            self.assertEqual(list(self.dest.parent.glob("*.git.*")), [])
        self.manifest.write_text("0" * 64 + "  config.sub\n")
        self.assertNotEqual(self.download().returncode, 0)
        self.assertFalse(self.dest.exists())
        self.assertEqual(list(self.dest.parent.glob("*.tmp.*")), [])
        self.assertEqual(list(self.dest.parent.glob("*.git.*")), [])

    def test_git_fetch_failure_has_bounded_retries_and_cleanup(self):
        commands = self.work / "commands"
        commands.mkdir()
        (commands / "timeout").write_text('#!/bin/sh\nprintf "attempt\\n" >> "$ATTEMPTS"\nexit 124\n')
        (commands / "sleep").write_text('#!/bin/sh\nexit 0\n')
        for path in commands.iterdir():
            path.chmod(0o755)
        attempts = self.work / "attempts"
        env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ["PATH"], ATTEMPTS=str(attempts))
        self.assertNotEqual(self.download(env=env).returncode, 0)
        self.assertEqual(len(attempts.read_text().splitlines()), 3)
        self.assertFalse(self.dest.exists())
        self.assertEqual(list(self.dest.parent.glob("*.git.*")), [])


class CompilerCache(Workspace):
    def setUp(self):
        super().setUp()
        self.toolchain = self.work / "obj_gcc/compiler with spaces"
        self.toolchain.mkdir(parents=True)
        self.compiler = self.toolchain / "gcc"
        self.compiler.write_text('#!/bin/sh\nexec ' + shlex.quote(shutil.which("cc")) + ' "$@"\n')
        self.compiler.chmod(0o755)
        for name in ["cc1", "cc1plus"]:
            (self.toolchain / name).write_text("frontend v1\n")
        self.script = str(ROOT / "scripts/compiler-cache.sh")

    def namespace(self):
        result = self.ok(run("sh", self.script, "ccache", str(self.compiler), sys.executable,
                             "-c", "import os; print(os.environ['CCACHE_NAMESPACE'])"))
        return result.stdout.strip()

    def test_frontend_content_changes_namespace_but_timestamps_do_not(self):
        before = self.namespace()
        old = self.compiler.stat()
        os.utime(self.compiler, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
        self.assertEqual(self.namespace(), before)
        (self.toolchain / "cc1plus").write_text("frontend v2\n")
        self.assertNotEqual(self.namespace(), before)

    def test_bootstrap_assembler_changes_namespace(self):
        assembler = self.work / "obj_binutils/gas/as-new"
        assembler.parent.mkdir(parents=True, exist_ok=True)
        assembler.write_text("assembler v1\n")
        before = self.namespace()
        old = assembler.stat()
        os.utime(assembler, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
        self.assertEqual(self.namespace(), before)
        assembler.write_text("assembler v2\n")
        self.assertNotEqual(self.namespace(), before)

    def test_without_ccache_command_arguments_and_status_are_preserved(self):
        result = run("sh", self.script, "", str(self.work / "absent compiler"), sys.executable,
                     "-c", "import json, sys; print(json.dumps(sys.argv[1:])); sys.exit(17)", "a b", "*.c")
        self.assertEqual(result.returncode, 17)
        self.assertEqual(json.loads(result.stdout), ["a b", "*.c"])

    def test_real_cache_hits_survive_timestamp_change_and_invalidate_on_frontend_change(self):
        cache = os.environ.get("CCACHE_TEST_BINARY") or shutil.which("ccache")
        if not cache:
            self.skipTest("host ccache required for actual cache-hit verification")
        env = {key: value for key, value in os.environ.items() if not key.startswith("CCACHE_")}
        env.update(CCACHE_DIR=str(self.work / "cache"), CCACHE_CONFIGPATH=str(self.work / "ccache.conf"),
                   CCACHE_COMPILERCHECK="content")
        source = self.work / "input.c"
        source.write_text("int cache_test(int x) { return x + 42; }\n")
        output = self.work / "output.o"

        def compile_source():
            output.unlink(missing_ok=True)
            self.ok(run("sh", self.script, cache, str(self.compiler), cache, str(self.compiler),
                        "-c", str(source), "-o", str(output), env=env))
            self.assertGreater(output.stat().st_size, 0)

        def hits():
            stats = dict(line.split() for line in self.ok(run(cache, "--print-stats", env=env)).stdout.splitlines())
            return sum(int(stats.get(name, 0)) for name in ["direct_cache_hit", "preprocessed_cache_hit"])

        compile_source()
        before = hits()
        old = self.compiler.stat()
        os.utime(self.compiler, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
        compile_source()
        self.assertEqual(hits(), before + 1)
        (self.toolchain / "cc1").write_text("frontend changed\n")
        before = hits()
        compile_source()
        self.assertEqual(hits(), before)
        compile_source()
        self.assertEqual(hits(), before + 1)


class ChrootCache(Workspace):
    def test_chroot_installer_preserves_cache_settings_and_architecture(self):
        # Capture the real wrapper's installer arguments without entering a chroot.
        installer = self.work / "alpine-chroot-install"
        installer.write_text('#!' + sys.executable + '\nimport json, sys\n'
                             'from pathlib import Path\nPath("arguments.json").write_text(json.dumps(sys.argv[1:]))\n')
        installer.chmod(0o755)
        self.ok(run("make", "--no-print-directory", "-B", "-f", str(ROOT / "GNUmakefile"),
                    "chroot", cwd=self.work))
        arguments = json.loads((self.work / "arguments.json").read_text())
        keep = arguments[arguments.index("-k") + 1]
        self.assertIn("git", arguments[arguments.index("-p") + 1].split())
        source = (ROOT / "alpine-chroot-install").read_text()
        start = source.index("gen_chroot_script() {")
        end = source.index("\n}\n", start) + 3
        env = dict(os.environ, CHROOT_KEEP_VARS=keep, QEMU_EMULATOR="",
                   ARCH="arm-linux-musleabihf", CI="true", CCACHE_DIR="/workspace/cache",
                   CCACHE_COMPILERCHECK="content", DONT_FORWARD_THIS="private")
        script = self.ok(run("sh", "-c", source[start:end] + "\ngen_chroot_script", env=env)).stdout
        generated = self.work / "alpine/enter-chroot"
        generated.parent.mkdir()
        generated.write_text(script)
        commands = self.work / "commands"
        commands.mkdir()
        (commands / "id").write_text('#!/bin/sh\nprintf "0\\n"\n')
        (commands / "chroot").write_text('#!/bin/sh\nexec /usr/bin/env -i /bin/sh -c ". ./env.sh; env"\n')
        for path in commands.iterdir():
            path.chmod(0o755)
        env["PATH"] = str(commands) + os.pathsep + os.environ["PATH"]
        result = self.ok(run("sh", str(generated), "ignored", cwd=self.work, env=env))
        values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        self.assertEqual(values["CCACHE_DIR"], "/workspace/cache")
        self.assertEqual(values["CCACHE_COMPILERCHECK"], "content")
        self.assertEqual(values["ARCH"], "arm-linux-musleabihf")
        self.assertEqual(values["CI"], "true")
        self.assertNotIn("DONT_FORWARD_THIS", values)

    def test_ci_cache_keys_are_per_target_and_stable_across_commits(self):
        import yaml
        workflow = yaml.load((ROOT / ".github/workflows/main.yml").read_text(), Loader=yaml.BaseLoader)
        job = workflow["jobs"]["gcc-musl-build"]
        step = next(s for s in job["steps"] if s.get("uses", "").startswith("hendrikmuhs/ccache-action@"))
        key = step["with"]["key"]
        self.assertIn("matrix.target", key)
        self.assertIn("env.ALPINE_BRANCH", key)
        self.assertIn("env.BUILD_FLAVOR", key)
        self.assertNotIn("github.sha", key)
        self.assertNotIn("github.ref", key)
        self.assertEqual(job["env"]["CCACHE_COMPILERCHECK"], "content")
        self.assertEqual(job["env"]["CCACHE_DIR"], "${{ github.workspace }}/.cache/ccache")


if __name__ == "__main__":
    unittest.main()
