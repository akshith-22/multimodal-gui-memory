# Multimodal Memory for GUI Agents Under Perturbation

CSE 598 group research project using AndroidReality, Mobile-Agent-v3's
GUIOwl agent implementation, and ASU's hosted Qwen3-VL API.

## Current implementation

- Baseline, text-memory, and multimodal-memory modes.
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
A fresh installation on a teammate's machine still needs verification.

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

For memory comparisons, change GUI_MEMORY_MODE to text or multimodal
before rerunning the block. Keep task instances, budgets, preprocessing,
and perturbation settings matched.

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
