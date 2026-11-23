"""Patches android_env 1.2.3 so APK installs work on Windows.

android_env writes the accessibility-forwarder APK to a NamedTemporaryFile and
calls `adb install` while the file is still open. On Windows the open file is
locked (and may not be flushed), so adb fails with "failed to open ... .apk:
No such file or directory". This patch writes and closes the file first, then
installs it and deletes it.

Run once after installing requirements, with the virtual environment active:

    python scripts/windows/patch_android_env.py

The script is idempotent. Pass a file path to patch a specific copy instead of
the installed module.
"""

import pathlib
import sys

MARKER = 'Local Windows patch: write and close the temp file'

ORIGINAL = """        with tempfile.NamedTemporaryFile(**kwargs) as f:
          fpath = f.name
          f.write(install_apk.blob.contents)

          response, _ = self._execute_command(
              ['install', '-r', '-t', '-g', fpath], timeout=timeout
          )"""

PATCHED = """        # Local Windows patch: write and close the temp file before calling
        # adb, because Windows locks open NamedTemporaryFiles and the data
        # may not be flushed yet. Original code kept the file open.
        del kwargs
        with tempfile.NamedTemporaryFile(suffix='.apk', delete=False) as f:
          fpath = f.name
          f.write(install_apk.blob.contents)
        try:
          response, _ = self._execute_command(
              ['install', '-r', '-t', '-g', fpath], timeout=timeout
          )
        finally:
          try:
            os.remove(fpath)
          except OSError:
            pass"""


def main() -> int:
  if len(sys.argv) > 1:
    target = pathlib.Path(sys.argv[1])
  else:
    from android_env.components import adb_call_parser  # pylint: disable=g-import-not-at-top
    target = pathlib.Path(adb_call_parser.__file__)

  source = target.read_text(encoding='utf-8')
  if MARKER in source:
    print(f'Already patched: {target}')
    return 0
  if source.count(ORIGINAL) != 1:
    print(f'Expected code block not found in {target}; no changes made.')
    print('Check the installed android_env version (expected 1.2.3).')
    return 1
  target.write_text(source.replace(ORIGINAL, PATCHED, 1), encoding='utf-8')
  print(f'Patched: {target}')
  return 0


if __name__ == '__main__':
  sys.exit(main())
