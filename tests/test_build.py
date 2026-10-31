"""Offline behavioral regression tests for downloads, builds and publication."""
import hashlib
import http.server
import io
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import threading
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, env=None):
    return subprocess.run(args, cwd=cwd, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


class Workspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dyne-test-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout)
        return result


class Downloads(Workspace):
    def setUp(self):
        super().setUp()
        self.payload = b"verified source archive\n"
        self.manifest = self.work / "sources.sha256"
        self.manifest.write_text(hashlib.sha256(self.payload).hexdigest() + "  source.tar.gz\n")
        self.dest = self.work / "directory with spaces/source.tar.gz"
        payload = self.payload

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(404 if self.path == "/missing" else 200)
                self.end_headers()
                self.wfile.write(b"wrong bytes" if self.path == "/wrong" else payload)

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def download(self, path="/source"):
        url = f"http://127.0.0.1:{self.server.server_port}{path}"
        return run("sh", str(ROOT / "scripts/download.sh"), url,
                   str(self.dest), str(self.manifest))

    def test_download_and_cached_reuse_preserve_mtime(self):
        self.ok(self.download())
        before = self.dest.stat().st_mtime_ns
        self.ok(self.download("/missing"))  # Cached input must not need a network request.
        self.assertEqual(self.dest.read_bytes(), self.payload)
        self.assertEqual(self.dest.stat().st_mtime_ns, before)

    def test_corrupted_cached_file_is_rejected(self):
        self.dest.parent.mkdir()
        self.dest.write_bytes(b"corrupted")
        self.assertNotEqual(self.download().returncode, 0)
        self.assertEqual(self.dest.read_bytes(), b"corrupted")

    def test_http_error_does_not_publish_a_file(self):
        self.assertNotEqual(self.download("/missing").returncode, 0)
        self.assertFalse(self.dest.exists())
        self.assertEqual(list(self.dest.parent.glob("*.tmp.*")), [])

    def test_wrong_digest_does_not_publish_a_file(self):
        self.assertNotEqual(self.download("/wrong").returncode, 0)
        self.assertFalse(self.dest.exists())
        self.assertEqual(list(self.dest.parent.glob("*.tmp.*")), [])

    def test_unknown_or_duplicate_digest_fails_closed(self):
        self.manifest.write_text("")
        self.assertNotEqual(self.download().returncode, 0)
        self.manifest.write_text(("0" * 64 + "  source.tar.gz\n") * 2)
        self.assertNotEqual(self.download().returncode, 0)
        self.assertFalse(self.dest.exists())

    def test_url_manifest_download_and_explicit_mirror_override(self):
        urls = self.work / "sources.urls"
        base = f"http://127.0.0.1:{self.server.server_port}"
        urls.write_text(f"source.tar.gz {base}/source\n")
        self.ok(run("sh", str(ROOT / "scripts/download.sh"), "", str(self.dest),
                    str(self.manifest), "source.tar.gz", str(urls)))
        self.assertEqual(self.dest.read_bytes(), self.payload)
        self.dest.unlink()
        # An explicit URL takes precedence, including when the manifest is absent.
        self.ok(run("sh", str(ROOT / "scripts/download.sh"), base + "/source",
                    str(self.dest), str(self.manifest), "source.tar.gz", str(self.work / "absent")))

    def test_missing_duplicate_or_invalid_url_fails_closed(self):
        urls = self.work / "sources.urls"
        for entries in ["", "source.tar.gz file:///etc/passwd\n",
                        "source.tar.gz https://example.org/a\n" * 2]:
            urls.write_text(entries)
            result = run("sh", str(ROOT / "scripts/download.sh"), "", str(self.dest),
                         str(self.manifest), "source.tar.gz", str(urls))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing or invalid source URL entry", result.stdout)
            self.assertFalse(self.dest.exists())


class LibraryBuilds(Workspace):
    """Use real Make dependencies/extraction with lightweight install fixtures."""
    def setUp(self):
        super().setUp()
        (self.work / "libs").mkdir()
        shutil.copy(ROOT / "GNUmakefile", self.work / "GNUmakefile")
        shutil.copytree(ROOT / "scripts", self.work / "scripts")
        shutil.copy(ROOT / "settings.cmake", self.work / "settings.cmake")
        cache = self.work / ".cache/sources"
        cache.mkdir(parents=True)
        recipe = (ROOT / "libs/GNUmakefile").read_text()
        packages = dict(re.findall(r"^(LIBSSL|ZLIB|CURL|SSH2|CCACHE|NCURSES|KYOTOCAB) \?= (\S+)$",
                                   recipe, re.MULTILINE))
        archives = [packages[key] + suffix for key, suffix in
                    [("LIBSSL", ".tar.gz"), ("ZLIB", ".tar.gz"), ("CURL", ".tar.xz"),
                     ("SSH2", ".tar.xz"), ("CCACHE", ".tar.xz"), ("NCURSES", ".tar.gz"),
                     ("KYOTOCAB", ".tar.gz")]]
        self.ssl_package = packages["LIBSSL"]
        self.curl_archive = packages["CURL"] + ".tar.xz"
        manifest = []
        for name in archives:
            with tarfile.open(cache / name, "w:gz" if name.endswith(".gz") else "w:xz") as archive:
                content = b"source fixture\n"
                member = tarfile.TarInfo(name.split(".tar.")[0] + "/input")
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))
            manifest.append(hashlib.sha256((cache / name).read_bytes()).hexdigest() + "  " + name)
        (self.work / "sources.sha256").write_text("\n".join(manifest) + "\n")
        compiler = self.work / "dyne/gcc-musl/bin"
        compiler.mkdir(parents=True)
        for arch in ["x86_64-linux-musl", "arm-linux-musleabihf"]:
            (compiler / (arch + "-gcc")).write_text("compiler fixture")
        recipe += '\n$(T)/lib/libssl.a $(T)/lib/libcrypto.a &:\n'
        recipe += '\t@mkdir -p "$(T)/lib"\n\t@touch "$(T)/lib/libssl.a" "$(T)/lib/libcrypto.a"\n'
        recipe += '\t@echo ssl >> "$(T)/order"\n'
        for output, name in [("lib/libz.a", "z"), ("lib/libssh2.a", "ssh"),
                             ("lib/libcurl.a", "curl"), ("lib/libncursesw.a", "ncurses"),
                             ("lib/libkyotocabinet.a", "kyoto"), ("bin/ccache", "ccache")]:
            recipe += f'\n$(T)/{output}:\n\t@mkdir -p "$(T)/lib" "$(T)/bin"\n'
            if name == "curl":
                recipe += '\t@test -f "$(T)/lib/libssh2.a" && test -f "$(T)/lib/libz.a"\n'
            recipe += f'\t@touch "$@"\n\t@echo {name} >> "$(T)/order"\n'
        (self.work / "libs/GNUmakefile").write_text(recipe)
        with (self.work / "GNUmakefile").open("a") as f:
            f.write('\ngcc:\n\t@echo gcc >> gcc-invocations\n')
        self.target = self.work / "dyne/x86_64-linux-musl"

    def make(self, *args):
        return self.ok(run("make", "--no-print-directory", "-j4", *args, cwd=self.work))

    def order(self):
        return (self.target / "order").read_text().splitlines()

    def test_existing_ssl_does_not_skip_other_packages_and_repeat_is_noop(self):
        (self.target / "lib").mkdir(parents=True)
        (self.target / "lib/libssl.a").touch()
        self.make("libs")
        first = self.order()
        self.assertEqual(set(first), {"ssl", "z", "ssh", "curl", "ncurses", "kyoto", "ccache"})
        self.assertLess(first.index("ssl"), first.index("ssh"))
        self.assertLess(first.index("ssh"), first.index("curl"))
        self.make("libs")
        self.assertEqual(self.order(), first)
        self.assertEqual((self.work / "gcc-invocations").read_text().splitlines(), ["gcc", "gcc"])

    def test_missing_compiler_fails_before_clearing_staged_libraries(self):
        self.target.mkdir(parents=True)
        marker = self.target / "keep-on-preflight-failure"
        marker.write_text("previous build\n")
        (self.work / "dyne/gcc-musl/bin/x86_64-linux-musl-gcc").unlink()
        result = run("make", "libs", cwd=self.work)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "previous build\n")

    def test_missing_crypto_rebuilds_ssl_and_dependents(self):
        self.make("libs")
        before = len(self.order())
        (self.target / "lib/libcrypto.a").unlink()
        self.make("libs")
        self.assertEqual(self.order()[before:], ["ssl", "ssh", "curl"])

    def test_flags_rebuild_and_target_build_directories_are_isolated(self):
        self.make("libs")
        before = (self.target / "lib/libcurl.a").stat().st_mtime_ns
        (self.target / "obsolete-header.h").touch()
        self.make("libs", "CFLAGS=-Os -DCHANGED")
        self.assertEqual(len(self.order()), 7)
        self.assertGreater((self.target / "lib/libcurl.a").stat().st_mtime_ns, before)
        self.assertFalse((self.target / "obsolete-header.h").exists())
        self.make("libs", "ARCH=arm-linux-musleabihf")
        for arch in ["x86_64-linux-musl", "arm-linux-musleabihf"]:
            self.assertTrue((self.work / "build/libs" / arch / self.ssl_package / "input").is_file())

    def test_clean_removes_headers_metadata_ncurses_and_kyoto(self):
        self.make("libs")
        (self.target / "include").mkdir()
        (self.target / "include/stale.h").touch()
        self.ok(run("make", "-C", "libs", "clean", cwd=self.work))
        self.assertFalse(self.target.exists())
        self.assertTrue((self.work / "libs/GNUmakefile").is_file())

    def test_cached_corruption_rejected_even_for_direct_installed_target(self):
        self.make("libs")
        (self.work / ".cache/sources" / self.curl_archive).write_bytes(b"bad cache")
        result = run("make", "-C", "libs", str(self.target / "lib/libcurl.a"), cwd=self.work)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed SHA-256 verification", result.stdout)

    def test_toolchain_source_state_change_rebuilds_libraries(self):
        self.make("libs")
        before = (self.target / "lib/libcurl.a").stat().st_mtime_ns
        state = self.work / "build/toolchain/x86_64-linux-musl/config"
        state.parent.mkdir(parents=True)
        state.write_text("updated libc source patch\n")
        self.make("libs")
        self.assertGreater((self.target / "lib/libcurl.a").stat().st_mtime_ns, before)


class ToolchainState(Workspace):
    def test_selected_sources_have_unique_urls_digests_and_compiler_catalog_entries(self):
        digests = {name: digest for digest, name in
                   (line.split() for line in (ROOT / "sources.sha256").read_text().splitlines())}
        urls = dict(line.split() for line in (ROOT / "sources.urls").read_text().splitlines())
        self.assertEqual(len(digests), len((ROOT / "sources.sha256").read_text().splitlines()))
        self.assertEqual(len(urls), len((ROOT / "sources.urls").read_text().splitlines()))
        self.assertEqual(set(urls), set(digests))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests.values()))
        self.assertTrue(all(url.startswith("https://") for url in urls.values()))
        probe = self.work / "sources.mk"
        probe.write_text('show-sources:\n\t@printf "%s\\n" $(ARCHIVES) config.sub.$(CONFIG_SUB_REV)\n')
        for flavor in ["static-small", "shared-optim"]:
            config = ROOT / "gcc-musl" / ("config." + flavor + ".mak")
            result = self.ok(run("make", "--no-print-directory", "-s", "-C", str(ROOT / "gcc-musl"),
                                 "-f", "Makefile", "-f", str(config), "-f", str(probe), "show-sources"))
            names = result.stdout.splitlines()
            self.assertEqual(len(names), 8)
            for name in names:
                self.assertIn(name, urls)
                self.assertTrue((ROOT / "gcc-musl/hashes" / (name + ".sha1")).is_file())

    def test_new_hashes_and_patches_are_visible_while_generated_sources_are_ignored(self):
        self.ok(run("git", "init", "-q", cwd=self.work))
        shutil.copy(ROOT / ".gitignore", self.work / ".gitignore")
        (self.work / "gcc-musl").mkdir()
        shutil.copy(ROOT / "gcc-musl/.gitignore", self.work / "gcc-musl/.gitignore")
        for name in ["gcc-musl/hashes/new.tar.xz.sha1", "gcc-musl/patches/gcc-99/fix.diff"]:
            self.assertNotEqual(run("git", "check-ignore", "-q", name, cwd=self.work).returncode, 0)
        for name in ["gcc-musl/gcc-99/source.c", "gcc-musl/config.mak", "gcc-musl/sources/gcc-99.tar.xz"]:
            self.ok(run("git", "check-ignore", "-q", name, cwd=self.work))

    def test_target_tuple_does_not_override_leaf_project_architecture(self):
        leaf = self.work / "leaf.mk"
        leaf.write_text('ARCH = x86_64\nleaf:\n\t@printf "%s\\n" "$(ARCH)" "$(CFLAGS)"\n')
        probe = self.work / "probe.mk"
        probe.write_text('probe:\n\t@$(MAKE) --no-print-directory -f ' + str(leaf) + ' leaf\n')
        result = self.ok(run("make", "--no-print-directory", "-C", str(ROOT / "gcc-musl"),
                             "-f", "Makefile", "-f", str(probe), "probe",
                             "ARCH=x86_64-linux-musl", "CFLAGS=-Os -DKEPT"))
        self.assertEqual(result.stdout, "x86_64\n-Os -DKEPT\n")

    def test_legacy_flavor_does_not_leak_into_musl_configure_arguments(self):
        fixture = self.work / "options.mk"
        fixture.write_text('show-options:\n\t@printf "%s\\n" "$(BUILD_FLAVOR)" "$(MUSL_CONFIG)"\n')
        result = self.ok(run("make", "--no-print-directory", "-f", str(ROOT / "GNUmakefile"),
                             "-f", str(fixture), "show-options", "MUSL_CONFIG=shared-optim"))
        self.assertEqual(result.stdout, "shared-optim\n\n")

    def test_legacy_flavor_child_receives_libc_flags_instead_of_flavor_name(self):
        fixture = self.work / "child.mk"
        fixture.write_text('show-child:\n\t@$(MAKE) --no-print-directory -s -C gcc-musl print-config\n')
        result = self.ok(run("make", "--no-print-directory", "-f", str(ROOT / "GNUmakefile"),
                             "-f", str(fixture), "show-child", "MUSL_CONFIG=static-small"))
        line = next(line for line in result.stdout.splitlines() if line.startswith("MUSL_CONFIG="))
        self.assertIn('-fPIC', line)
        self.assertNotIn('static-small', line)

    def test_external_sources_are_not_populated_or_modified(self):
        external = self.work / "immutable-sources"
        result = run("make", "-C", str(ROOT / "gcc-musl"), "fetch-sources", "SOURCES=" + str(external))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable SOURCES", result.stdout)
        self.assertFalse(external.exists())

    def test_changed_configuration_invalidates_only_selected_target(self):
        (self.work / "scripts").mkdir()
        shutil.copy(ROOT / "scripts/toolchain-state.sh", self.work / "scripts/toolchain-state.sh")
        for name in ["GNUmakefile", "sources.sha256", "gcc-musl/config.mak",
                     "gcc-musl/litecross/Makefile", "gcc-musl/patches/gcc/fix.diff"]:
            p = self.work / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("fixture\n")
        makefile = self.work / "gcc-musl/Makefile"
        makefile.write_text('print-config:\n\t@printf "%s\\n" "FLAGS=small"\n')
        script = str(ROOT / "scripts/toolchain-state.sh")
        arch = "arm-linux-musleabihf"
        self.ok(run("sh", script, arch, cwd=self.work))
        selected = self.work / "gcc-musl/build/local" / arch
        selected.mkdir(parents=True)
        (selected / ".lc_built").touch()
        other = self.work / "gcc-musl/build/local/x86_64-linux-musl"
        other.mkdir()
        self.ok(run("sh", script, arch, cwd=self.work))
        self.assertTrue((selected / ".lc_built").exists())
        (self.work / "gcc-musl/config.mak").write_text("changed flags\n")
        self.ok(run("sh", script, arch, cwd=self.work))
        self.assertFalse(selected.exists())
        self.assertTrue(other.exists())


class Preparation(Workspace):
    def setUp(self):
        super().setUp()
        self.arch = "arm-linux-musleabihf"
        self.compiler = self.work / "dyne/gcc-musl"
        self.target = self.work / "dyne" / self.arch
        (self.compiler / "bin").mkdir(parents=True)
        (self.compiler / self.arch / "lib").mkdir(parents=True)
        (self.target / "lib").mkdir(parents=True)
        (self.work / "README.md").write_text("[Documentation](https://example.org)\n")
        shutil.copy(ROOT / "settings.cmake", self.work / "settings.cmake")
        (self.work / "input.c").write_text("int main(void) {return 0;}\n")
        self.ok(run("cc", "input.c", "-o", str(self.compiler / "bin/compiler"), cwd=self.work))
        shutil.copy(self.compiler / "bin/compiler", self.target / "lib/a file with spaces")
        script = '#!/bin/sh\nprintf "%s\\n" "$*" >> "' + str(self.work / "stripped") + '"\n'
        self.stripper = self.compiler / "bin" / (self.arch + "-strip")
        self.stripper.write_text(script)
        self.stripper.chmod(0o755)
        self.host = self.work / "host-strip"
        self.host.write_text(script.replace("stripped", "host-stripped"))
        self.host.chmod(0o755)
        self.env = dict(os.environ, HOST_STRIP=str(self.host))

    def test_foreign_pruning_correct_strip_tools_and_readmes(self):
        for directory in [self.compiler / self.arch / "lib", self.target / "lib"]:
            (directory / "libbad.so.1").write_text("prune")
            (directory / "libbad.so").symlink_to("libbad.so.1")
            (directory / "libbad.la").write_text("prune")
        other = self.compiler / "x86_64-linux-musl/lib"
        other.mkdir(parents=True)
        (other / "libkeep.so").write_text("other target")
        self.ok(run("bash", str(ROOT / "prepare.sh"), self.arch, cwd=self.work, env=self.env))
        self.assertFalse((self.target / "lib/libbad.so").is_symlink())
        self.assertFalse((self.compiler / self.arch / "lib/libbad.so.1").exists())
        self.assertTrue((other / "libkeep.so").exists())
        self.assertIn("a file with spaces", (self.work / "stripped").read_text())
        self.assertIn("bin/compiler", (self.work / "host-stripped").read_text())
        self.assertEqual((self.compiler / "README.txt").read_text(), "Documentation\n")
        self.assertEqual((self.target / "README.txt").read_bytes(), (self.compiler / "README.txt").read_bytes())

    def test_strip_error_propagates(self):
        self.env["HOST_STRIP"] = "/bin/false"
        self.assertNotEqual(run("bash", str(ROOT / "prepare.sh"), self.arch,
                                cwd=self.work, env=self.env).returncode, 0)

    def test_host_binutils_inside_target_directory_use_host_strip(self):
        directory = self.compiler / self.arch / "bin"
        directory.mkdir()
        shutil.copy(self.compiler / "bin/compiler", directory / "readelf")
        self.ok(run("bash", str(ROOT / "prepare.sh"), self.arch, cwd=self.work, env=self.env))
        self.assertIn(self.arch + "/bin/readelf", (self.work / "host-stripped").read_text())
        self.assertNotIn(self.arch + "/bin/readelf", (self.work / "stripped").read_text())

    def test_invalid_target_is_rejected(self):
        self.assertNotEqual(run("bash", str(ROOT / "prepare.sh"), "../escape",
                                cwd=self.work, env=self.env).returncode, 0)


class Release(Workspace):
    def publication_step(self, draft):
        import yaml
        workflow = yaml.load((ROOT / ".github/workflows/main.yml").read_text(), Loader=yaml.BaseLoader)
        step = next(s for s in workflow["jobs"]["release"]["steps"]
                    if s.get("name") == "Stage GitHub release assets for recoverable publication")
        (self.work / "release-notes.txt").write_text("Release notes\n")
        executable = self.work / "gh"
        executable.write_text('#!/bin/sh\nif [ "$2" = view ]; then printf "%s\\n" "' + draft +
                              '"; else printf "%s\\n" "$*" >> operations; fi\n')
        executable.chmod(0o755)
        env = dict(os.environ, PATH=str(self.work) + os.pathsep + os.environ["PATH"], RELEASE_TAG="v1.2.3")
        return run("bash", "-e", "-o", "pipefail", "-c", step["run"], cwd=self.work, env=env)

    def test_published_assets_cannot_be_replaced(self):
        self.assertNotEqual(self.publication_step("false").returncode, 0)
        self.assertFalse((self.work / "operations").exists())

    def test_draft_assets_can_be_retried(self):
        self.ok(self.publication_step("true"))
        self.assertIn("release upload v1.2.3", (self.work / "operations").read_text())

    def test_archive_rejects_missing_layout_shared_libraries_and_path_traversal(self):
        spec = importlib.util.spec_from_file_location("check_archive", ROOT / "scripts/check-archive.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        for name in ["dyne/README.txt", "../escape", "dyne/arm-linux-musleabihf/lib/libbad.so.1"]:
            archive = self.work / "bad.tar.xz"
            with tarfile.open(archive, "w:xz") as output:
                entry = tarfile.TarInfo(name)
                entry.size = 1
                output.addfile(entry, io.BytesIO(b"x"))
            with self.assertRaises(ValueError):
                checker.check("arm-linux-musleabihf", archive)

    def test_manifest_has_exactly_four_archive_hashes_and_reruns_cleanly(self):
        for suffix in ["x86_64", "arm_hf", "arm_64", "riscv_64"]:
            (self.work / ("dyne-gcc-musl-" + suffix + ".tar.xz")).write_bytes(suffix.encode())
        script = str(ROOT / "scripts/release-checksums.sh")
        self.ok(run("bash", script, str(self.work)))
        first = (self.work / "SHA256SUMS.txt").read_bytes()
        self.assertEqual(len(first.splitlines()), 4)
        self.ok(run("bash", script, str(self.work)))
        self.assertEqual((self.work / "SHA256SUMS.txt").read_bytes(), first)
        (self.work / "dyne-gcc-musl-arm_hf.tar.xz").unlink()
        self.assertNotEqual(run("bash", script, str(self.work)).returncode, 0)

    def test_retry_tag_must_match_built_commit(self):
        self.ok(run("git", "init", "-q", cwd=self.work))
        for name, value in [("user.name", "Fixture"), ("user.email", "test@example.org")]:
            self.ok(run("git", "config", name, value, cwd=self.work))
        self.ok(run("git", "commit", "--allow-empty", "-m", "one", cwd=self.work))
        self.ok(run("git", "tag", "v1.0.0", cwd=self.work))
        script = str(ROOT / "scripts/assert-release-tag.sh")
        self.ok(run("bash", script, "v1.0.0", "HEAD", cwd=self.work))
        self.ok(run("git", "commit", "--allow-empty", "-m", "two", cwd=self.work))
        self.assertNotEqual(run("bash", script, "v1.0.0", "HEAD", cwd=self.work).returncode, 0)
        self.assertNotEqual(run("bash", script, "1.0.0", "HEAD", cwd=self.work).returncode, 0)

    def test_release_graph_validates_before_tagging_and_never_deletes_tags(self):
        import yaml
        workflow = yaml.load((ROOT / ".github/workflows/main.yml").read_text(), Loader=yaml.BaseLoader)
        jobs = workflow["jobs"]
        self.assertIn("pull_request", workflow["on"])
        self.assertEqual(jobs["gcc-musl-build"]["needs"], "checks")
        self.assertNotIn("if", jobs["gcc-musl-build"])
        self.assertIn("gcc-musl-build", jobs["release"]["needs"])
        self.assertFalse(any("delete-tag" in json.dumps(job) for job in jobs.values()))
        config = json.loads((ROOT / ".releaserc").read_text())
        self.assertEqual(config["tagFormat"], "v${version}")
        steps = jobs["release"]["steps"]
        checksum = next(i for i, s in enumerate(steps) if "release-checksums.sh" in s.get("run", ""))
        tagging = next(i for i, s in enumerate(steps) if s.get("id") == "semantic-release")
        self.assertLess(checksum, tagging)


class CMakeSettings(Workspace):
    def test_documented_install_option_sysroot_and_user_flags(self):
        (self.work / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.20)\nproject(Fixture NONE)\n'
            'file(WRITE "${CMAKE_BINARY_DIR}/result" '
            '"${CMAKE_INSTALL_PREFIX}\\n${CMAKE_SYSROOT}\\n${CMAKE_C_FLAGS}\\n${CMAKE_SYSTEM_PROCESSOR}")\n')
        self.ok(run("cmake", "-S", str(self.work), "-B", str(self.work / "build"),
                    "-DCMAKE_TOOLCHAIN_FILE=" + str(ROOT / "settings.cmake"),
                    "-DROOT=" + str(self.work), "-DARCH=aarch64-linux-musl",
                    "-DCCACHE=OFF", "-DFOR_MUSL_DYNE=ON", "-DCMAKE_C_FLAGS=-DCUSTOM"))
        values = (self.work / "build/result").read_text().splitlines()
        self.assertEqual(values, [str(self.work / "dyne/aarch64-linux-musl"),
                                  str(self.work / "dyne/gcc-musl/aarch64-linux-musl"),
                                  "-DCUSTOM", "aarch64"])


if __name__ == "__main__":
    unittest.main()
