"""Regression coverage for build-host paths in published library metadata."""

import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('relocation', ROOT / 'scripts/relocate-metadata.py')
relocation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(relocation)


class Relocation(unittest.TestCase):
    def test_metadata_survives_a_second_move_and_repeated_preparation(self):
        with tempfile.TemporaryDirectory(prefix='dyne relocation ') as temporary:
            root = Path(temporary)
            prefix = root / 'original/x86_64-linux-musl'
            pc = prefix / 'lib/pkgconfig/example.pc'
            cmake = prefix / 'lib/cmake/example/exampleConfig.cmake'
            pc.parent.mkdir(parents=True)
            cmake.parent.mkdir(parents=True)
            config = prefix / 'bin/curl-config'
            config.parent.mkdir()
            old = '/home/runner/work/musl/musl/dyne/x86_64-linux-musl'
            pc.write_text(f'prefix={old}\nlibdir=${{prefix}}/lib\nincludedir=${{prefix}}/include\n'
                          'Name: example\nDescription: relocation fixture\nVersion: 1\n'
                          f'Libs: -L${{libdir}} -lexample\nLibs.private: {old}/lib/libdependency.a\n')
            cmake.write_text(f'set(EXAMPLE_ARCHIVE "{old}/lib/libexample.a")\n')
            config.write_text(f"#!/bin/sh\nprefix='{old}'\n"
                              'if [ "$1" = --prefix ]; then echo "$prefix"; else\n'
                              f"echo '{Path(old).parent}/gcc-musl/bin/x86_64-linux-musl-gcc'\nfi\n")
            config.chmod(0o755)
            self.assertEqual(len(relocation.relocate(prefix)), 3)
            self.assertEqual(relocation.relocate(prefix), [])
            moved = root / 'relocated/x86_64-linux-musl'
            moved.parent.mkdir()
            shutil.move(prefix, moved)
            self.assertFalse(prefix.exists())
            self.assertEqual(relocation.relocate(moved), [])
            config = moved / 'bin/curl-config'
            reported = subprocess.check_output([config, '--prefix'], text=True).strip()
            self.assertEqual(Path(reported), moved)
            reported = subprocess.check_output([config, '--cc'], text=True).strip()
            self.assertEqual(Path(reported).resolve(), moved.parent / 'gcc-musl/bin/x86_64-linux-musl-gcc')
            check = root / 'check.cmake'
            check.write_text(f'include("{moved}/lib/cmake/example/exampleConfig.cmake")\n'
                             f'get_filename_component(archive "${{EXAMPLE_ARCHIVE}}" ABSOLUTE)\n'
                             f'if(NOT archive STREQUAL "{moved}/lib/libexample.a")\n'
                             '  message(FATAL_ERROR "Stale CMake archive: ${archive}")\nendif()\n')
            result = subprocess.run(['cmake', '-P', check], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            env = dict(os.environ, PKG_CONFIG_LIBDIR=str(moved / 'lib/pkgconfig'), PKG_CONFIG_PATH='', PKG_CONFIG_SYSROOT_DIR='')
            result = subprocess.run(['pkg-config', '--dont-define-prefix', '--static', '--libs', 'example'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('/home/runner', result.stdout)
            flags = shlex.split(result.stdout)
            self.assertEqual(Path(next(flag[2:] for flag in flags if flag.startswith('-L'))).resolve(), moved / 'lib')

    def test_selected_target_only_and_existing_relative_metadata_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selected = root / 'arm-linux-musleabihf'
            other = root / 'x86_64-linux-musl/lib/pkgconfig/other.pc'
            pc = selected / 'lib/pkgconfig/relative.pc'
            pc.parent.mkdir(parents=True)
            other.parent.mkdir(parents=True)
            other.write_text('prefix=/old/x86_64-linux-musl\n')
            pc.write_text('prefix=${pcfiledir}/../..\nLibs: -L${prefix}/lib -lrelative\n')
            self.assertEqual(relocation.relocate(selected), [])
            self.assertEqual(other.read_text(), 'prefix=/old/x86_64-linux-musl\n')
