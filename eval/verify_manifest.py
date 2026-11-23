"""Checks that eval/manifest.yaml matches the task instances this code generates.

Run from the repository root with the virtual environment active:

    python eval/verify_manifest.py

No emulator or API key is needed. Exits with status 1 if any goal differs.
"""

import contextlib
import io
import os
import sys
import warnings

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'MobileAgent', 'Mobile-Agent-v3', 'android_world_v3'))
warnings.filterwarnings('ignore')

with contextlib.redirect_stdout(io.StringIO()):
  from android_world import registry, suite_utils  # pylint: disable=g-import-not-at-top


def main() -> int:
  with open(os.path.join(ROOT, 'eval', 'manifest.yaml'), encoding='utf-8') as f:
    manifest = yaml.safe_load(f)

  task_registry = registry.TaskRegistry().get_registry(
      registry.TaskRegistry.ANDROID_WORLD_FAMILY
  )
  failures = 0
  for split_name, split in manifest['splits'].items():
    tasks = sorted({inst['task'] for inst in split['instances']})
    with contextlib.redirect_stdout(io.StringIO()):
      suite = suite_utils.create_suite(
          task_registry,
          n_task_combinations=split['n_task_combinations'],
          seed=split['task_random_seed'],
          tasks=tasks,
      )
    for inst in split['instances']:
      generated = suite[inst['task']][inst['index']]
      budget = manifest['budgets'][inst['task']]
      ok = generated.goal == inst['goal']
      ok_budget = int(10 * generated.complexity) == budget['default']
      status = 'OK ' if ok and ok_budget else 'MISMATCH'
      print(f"{status} {split_name:12s} {inst['task']}[{inst['index']}]")
      if not ok:
        print(f'    manifest : {inst["goal"]!r}\n    generated: {generated.goal!r}')
      if not ok_budget:
        print(f"    budget   : manifest {budget['default']}, code {int(10 * generated.complexity)}")
      failures += not (ok and ok_budget)

  print('All instances match.' if not failures else f'{failures} mismatch(es).')
  return 1 if failures else 0


if __name__ == '__main__':
  sys.exit(main())
