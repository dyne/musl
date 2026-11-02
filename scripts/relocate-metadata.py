#!/usr/bin/env python3
"""Make installed library metadata and shell config helpers relocatable."""

import argparse
import os
from pathlib import Path
import re


def relocate(prefix):
    prefix = Path(prefix).resolve()
    pcfiles = sorted((prefix / 'lib/pkgconfig').glob('*.pc'))
    configfiles = [path for path in sorted((prefix / 'bin').glob('*-config'))
                   if path.is_file() and path.read_bytes().startswith(b'#!')]
    old_prefixes = {str(prefix)}
    for path in pcfiles + configfiles:
        match = re.search(r'''^prefix=['"]?(/[^'"\r\n]+)['"]?$''', path.read_text(), re.MULTILINE)
        if match and Path(match[1]).name == prefix.name:
            old_prefixes.add(match[1].rstrip('/'))
    changed = []
    for path in pcfiles + sorted((prefix / 'lib/cmake').rglob('*.cmake')):
        original = path.read_text()
        text = original
        if path.suffix == '.pc':
            for old in sorted(old_prefixes, key=len, reverse=True):
                text = text.replace(old, '${prefix}')
            text = re.sub(r'^prefix=.*$', 'prefix=${pcfiledir}/../..', text, flags=re.MULTILINE)
        else:
            relative = os.path.relpath(prefix, path.parent).replace(os.sep, '/')
            for old in sorted(old_prefixes, key=len, reverse=True):
                text = text.replace(old, '${CMAKE_CURRENT_LIST_DIR}/' + relative)
        if text != original:
            path.write_text(text)
            changed.append(str(path.relative_to(prefix)))
    for path in configfiles:
        original = path.read_text()
        text = original
        if not any(old in text or str(Path(old).parent / 'gcc-musl') in text for old in old_prefixes):
            continue
        text = re.sub(r'^prefix=.*$',
                      'prefix=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)',
                      text, flags=re.MULTILINE)
        for old in sorted(old_prefixes, key=len, reverse=True):
            compiler = str(Path(old).parent / 'gcc-musl')
            for source, replacement in [(old, '${prefix}'), (compiler, '${prefix}/../gcc-musl')]:
                # Convert literal single-quoted paths to expandable double quotes.
                pattern = r'''(['"])''' + re.escape(source) + r'''([^'"]*)\1'''
                text = re.sub(pattern, lambda match: '"' + replacement + match[2] + '"', text)
                text = text.replace(source, replacement)
        if text != original:
            path.write_text(text)
            changed.append(str(path.relative_to(prefix)))
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path)
    args = parser.parse_args()
    for name in relocate(args.prefix):
        print(name)
