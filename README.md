# Multimodal Memory for GUI Agents Under Perturbation

CSE 598 group research project using AndroidReality, Mobile-Agent-v3's
GUIOwl agent implementation, and ASU's hosted Qwen3-VL API.

## Current implementation

- Baseline, text-memory, multimodal-memory, and perturbation-aware memory
  modes (`GUI_MEMORY_MODE=baseline|text|multimodal|perturbation`).
- Perturbation-aware memory detects possibly lost progress and excludes
  stale history (see `android_world/agents/perturbation_memory.py`).
- Memory retrieval and action/observation trace logging.
- More tolerant conclusion parsing.
- Actions routed through the environment to activate perturbation wrappers.
- JPEG image-size limits and immediate failure on HTTP 413.
- Optional diagnostic step-budget override.

The backend is qwen3-vl-32b, not the original GUI-Owl model weights.

## Environment

The current pilot was run on an Apple Silicon Mac with Python 3.11,
Android Studio, and an Android 13 / API 33 ARM64 emulator.

requirements-mac-pilot.txt captures the working environment.
A fresh installation was verified on Windows 11 (x86_64); see
"Windows 11 setup" below for the differences.

## Installation

From this repository's root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-mac-pilot.txt
python -m pip install --no-deps -e MobileAgent/Mobile-Agent-v3/android_world_v3
```

For this project, use the bundled Mobile-Agent-v3 AndroidWorld fork.
See its README for emulator provisioning and AndroidWorld app setup.
Creating an empty AVD alone does not install the benchmark apps.

## Emulator

On the pilot Mac, the provisioned AVD is named AndroidWorldAvd.
In a separate terminal:

```bash
"$HOME/Library/Android/sdk/emulator/emulator" \
  -avd AndroidWorldAvd -no-snapshot -grpc 8554
```

Check connectivity:

```bash
"$HOME/Library/Android/sdk/platform-tools/adb" devices
```

Expected device: emulator-5554.
Paths and system images must be adapted for other operating systems.

## API key

Each member supplies their own ASU API key.
Never commit keys or paste them into shared logs.

In macOS zsh:

```bash
read -rs "ASU_API_KEY?ASU API key: "
echo
export ASU_API_KEY
```

## One clean pilot episode

Run from the repository root with the virtual environment active
and the provisioned emulator running:

```bash
export PYTHONPATH="$PWD/MobileAgent/Mobile-Agent-v3/android_world_v3"
export GUI_MEMORY_MODE=baseline
export GUI_MEMORY_TOP_K=2
unset GUI_DIAGNOSTIC_MAX_STEPS

"$HOME/Library/Android/sdk/platform-tools/adb" \
  -s emulator-5554 shell settings put system font_scale 1.0

run_dir="$PWD/runs/contacts-${GUI_MEMORY_MODE}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$run_dir/results" "$run_dir/traces"

(
  set -o pipefail
  cd AndroidReality/perturbation
  python run_ma3.py \
    --suite_family=android_world \
    --tasks=ContactsAddContact \
    --agent_name=gui_owl \
    --base_url=https://openai.rc.asu.edu/v1 \
    --model=qwen3-vl-32b \
    --api_key="$ASU_API_KEY" \
    --guiowl_coordinate_format=qwen-vl \
    --console_port=5554 \
    --grpc_port=8554 \
    --mdp_font_size_enable=False \
    --mdp_state_reset_enable=False \
    --output_path="$run_dir/results" \
    --traj_output_path="$run_dir/traces" \
    2>&1 | tee "$run_dir/run.log"
)
```

For memory comparisons, change GUI_MEMORY_MODE to text, multimodal, or
perturbation before rerunning the block. Keep task instances, budgets, preprocessing,
and perturbation settings matched.

## Windows 11 setup

Verified on Windows 11 with an Intel CPU, Python 3.11.9, and an x86_64
Android 13 emulator. Commands are for PowerShell unless marked Git Bash.

1. Enable hardware acceleration. In an administrator PowerShell, run
   `Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All`
   and reboot.

2. Install Python 3.11 (a stale 3.12 registration without python.exe is a
   common trap; check with `py -0p`):

   ```powershell
   winget install --id Python.Python.3.11 --scope user
   ```

3. Install the Android SDK without Android Studio (Java 17 is required).
   Download the command-line tools from
   https://developer.android.com/studio#command-line-tools-only and unpack
   them so that this file exists:
   `%LOCALAPPDATA%\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat`.
   Accept the licenses from Git Bash, because piping `y` from PowerShell does
   not reach sdkmanager:

   ```bash
   SDK="$LOCALAPPDATA/Android/Sdk"
   yes | "$SDK/cmdline-tools/latest/bin/sdkmanager.bat" --licenses
   yes | "$SDK/cmdline-tools/latest/bin/sdkmanager.bat" platform-tools emulator \
     "platforms;android-33" "system-images;android-33;google_apis;x86_64"
   ```

4. Create the AVD (Git Bash), then raise its storage and RAM, because the
   default 800 MB data partition is too small for the AndroidWorld apps:

   ```bash
   echo no | "$SDK/cmdline-tools/latest/bin/avdmanager.bat" create avd \
     -n AndroidWorldAvd -k "system-images;android-33;google_apis;x86_64" -d pixel_6
   cfg="$USERPROFILE/.android/avd/AndroidWorldAvd.avd/config.ini"
   sed -i -e 's/^disk.dataPartition.size=.*/disk.dataPartition.size=8G/' \
          -e 's/^hw.ramSize=.*/hw.ramSize=4096M/' "$cfg"
   "$SDK/emulator/emulator.exe" -accel-check   # expect "WHPX ... usable"
   ```

5. Create the environment and apply the Windows patch for android_env:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements-mac-pilot.txt
   python scripts\windows\patch_android_env.py
   ```

   If activation is blocked, run
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
   The editable install of android_world is optional: `PYTHONPATH` already
   makes it importable. If you do run it, use
   `pip install "setuptools<81"` and `--no-build-isolation`, then restore the
   regenerated proto files with
   `git checkout -- MobileAgent/Mobile-Agent-v3/android_world_v3/android_world/task_evals/information_retrieval/proto/`.

6. Start the emulator in its own window and leave it open:

   ```powershell
   & "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd AndroidWorldAvd -no-snapshot -grpc 8554
   ```

7. Run an episode. `PYTHONUTF8=1` is required: without it the evaluator
   crashes while printing its result emoji and no result is saved. Add
   `--perform_emulator_setup=True` on the first run only, to install the
   AndroidWorld apps.

   ```powershell
   $s = Read-Host -AsSecureString "ASU API key"
   $env:ASU_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
   $env:PYTHONPATH = "$PWD\MobileAgent\Mobile-Agent-v3\android_world_v3"
   $env:PYTHONUTF8 = "1"
   $env:GUI_MEMORY_MODE = "baseline"; $env:GUI_MEMORY_TOP_K = "2"
   Remove-Item Env:GUI_DIAGNOSTIC_MAX_STEPS -ErrorAction SilentlyContinue
   $adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
   & $adb -s emulator-5554 shell settings put system font_scale 1.0
   $run = "$PWD\runs\contacts-baseline-$(Get-Date -Format yyyyMMdd-HHmmss)"
   New-Item -ItemType Directory -Force "$run\results","$run\traces" | Out-Null
   cd AndroidReality\perturbation
   python run_ma3.py --suite_family=android_world --tasks=ContactsAddContact --agent_name=gui_owl `
     --base_url=https://openai.rc.asu.edu/v1 --model=qwen3-vl-32b --api_key="$env:ASU_API_KEY" `
     --guiowl_coordinate_format=qwen-vl --adb_path="$adb" --console_port=5554 --grpc_port=8554 `
     --mdp_font_size_enable=False --mdp_state_reset_enable=False `
     --output_path="$run\results" --traj_output_path="$run\traces" 2>&1 | Tee-Object "$run\run.log"
   cd ..\..
   ```

   Windows PowerShell 5.1 shows Python warnings as red `NativeCommandError`
   text; that alone is not a failure. `Tee-Object` writes the log as UTF-16.
   The automatic Contacts app setup may report `"Don't allow" not found`;
   the agent can still dismiss the permission prompt itself.

Reproduction record (2026-11-23): commit 69c6ad9 plus the Windows changes
above, Windows 11 x86_64 emulator, clean baseline on ContactsAddContact
(Hugo Pereira): Task Successful, 12 steps, 119.6 s.

## Evaluation manifest

`eval/manifest.yaml` fixes the task instances, development/held-out split,
conditions, configurations, step budgets, and repetitions for the final
comparison. Task goals are generated deterministically from the task name and
seed. Check that the manifest still matches the code (no emulator needed):

```bash
python eval/verify_manifest.py
```

Run held-out instances only after the manifest's `frozen_commit` is set.

## Perturbation experiments

Add flags to the Python command before its output redirection.

Small font condition:

```text
--mdp_font_size_enable=True
--mdp_font_size_activation_mode=on_reset
--mdp_font_size_scale=0.82
--mdp_font_size_restore_on_close=True
```

Replace the clean command's font-enable flag rather than duplicating it.
Verify the actual emulator font scale during the run.

App reset after five ordinary actions:

```text
--mdp_state_reset_enable=True
--mdp_state_reset_trigger_steps=5
--mdp_state_reset_return_home=True
```

Replace the clean command's reset-enable flag.
For the exploratory 24-step condition, set:

```bash
export GUI_DIAGNOSTIC_MAX_STEPS=24
```

Unset this variable to restore the original benchmark budget.
Report these budget conditions separately.

## Results and limitations

Logs, evaluation outputs, screenshots, and memory traces are saved under runs/.
These generated files are excluded from Git.

Earlier clean/font pilots succeeded in all 18 comparison episodes,
but used one repeated ContactsAddContact instance and an earlier code version.

After action routing and JPEG changes, the exploratory 24-step reset pilot
showed baseline success and evaluated failures for both memory modes.
These are preliminary observations, not evidence of memory superiority.
Earlier and current code versions must not be treated as matched controls.

Memory records model summaries and screenshot changes.
A changed screenshot does not establish semantic action success.
Inspect evaluator results; a saved output directory does not prove success.

## Working together

Record the commit ID with every experiment:

```bash
git rev-parse HEAD
```

Use branches and pull requests for changes.
Keep code version, task parameters, memory settings, perturbations, budget,
and results together in each experiment's notes.

See UPSTREAM.md and retained upstream license files for attribution.
