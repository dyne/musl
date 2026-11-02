"""Exercise the CMake static-PIE probe with compilers rejecting non-PIE probes."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StaticPIE(unittest.TestCase):
    def configure(self, blocked=False):
        temporary = tempfile.TemporaryDirectory(prefix='dyne-pie-')
        self.addCleanup(temporary.cleanup)
        work = Path(temporary.name)
        wrapper = work / 'compiler'
        wrapper.write_text(f'#!{sys.executable}\n' + '''import json, os, sys
args = sys.argv[1:]
if any(arg in ('-DCMAKE_C_LINK_PIE_SUPPORTED', '-DCMAKE_CXX_LINK_PIE_SUPPORTED') for arg in args):
    with open(os.environ['PIE_PROBE_LOG'], 'a') as log:
        log.write(json.dumps(args) + '\\n')
    if '-fPIE' not in args or os.environ.get('PIE_PROBE_BLOCKED') == '1':
        print('PIE probe object is not relocatable', file=sys.stderr)
        sys.exit(1)
os.execv(os.environ['PIE_REAL_COMPILER'], [os.environ['PIE_REAL_COMPILER'], *args])
''')
        wrapper.chmod(0o755)
        (work / 'main.c').write_text('int main(void) { return 0; }\n')
        (work / 'CMakeLists.txt').write_text(
            'cmake_minimum_required(VERSION 3.22)\nproject(StaticPIEProbe C CXX)\n'
            'set(CMAKE_REQUIRED_FLAGS "-DDYNE_KEEP_REQUIRED_FLAG=1")\n'
            f'include("{ROOT}/tests/cmake/RequireStaticPIE.cmake")\n'
            'dyne_require_static_pie()\n'
            'if(NOT CMAKE_REQUIRED_FLAGS STREQUAL "-DDYNE_KEEP_REQUIRED_FLAG=1")\n'
            '  message(FATAL_ERROR "PIE flags leaked into other feature checks")\nendif()\n'
            'set(CMAKE_POSITION_INDEPENDENT_CODE ON)\nadd_executable(probe main.c)\n')
        env = dict(os.environ, PIE_REAL_COMPILER=shutil.which('cc'),
                   PIE_PROBE_LOG=str(work / 'probes.jsonl'), PIE_PROBE_BLOCKED=str(int(blocked)))
        result = subprocess.run(['cmake', '-S', str(work), '-B', str(work / 'build'),
                                 '-DCMAKE_C_COMPILER=' + str(wrapper),
                                 '-DCMAKE_CXX_COMPILER=' + str(wrapper)],
                                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return work, env, result

    def test_probes_compile_pie_objects_and_preserve_caller_flags(self):
        work, env, result = self.configure()
        self.assertEqual(result.returncode, 0, result.stdout)
        probes = [json.loads(line) for line in (work / 'probes.jsonl').read_text().splitlines()]
        self.assertEqual(len(probes), 2)
        for probe in probes:
            self.assertIn('-fPIE', probe)
            self.assertIn('-DDYNE_KEEP_REQUIRED_FLAG=1', probe)
        result = subprocess.run(['cmake', '--build', str(work / 'build')], env=env,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_failed_pie_support_stops_configuration_with_diagnostic(self):
        _, _, result = self.configure(blocked=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Static PIE link support is required', result.stdout)
        self.assertIn('PIE probe object is not relocatable', result.stdout)
