# GR00T-G1 Logging System

Comprehensive logging system to track the complete data flow from GR00T model predictions to robot execution.

## Overview

The logging system captures:
1. **Server-side**: Model inputs and outputs
2. **Client-side**: Observations sent, actions received, actions used
3. **Simulation-side**: Actions injected into robot, actual robot joint positions

## Log Files

All logs are saved to timestamped directories under `logs/`:

```
logs/YYYY-MM-DD_HH-MM-SS/TaskName/
├── client_actions.jsonl                      # Client communication logs
├── robot_states.jsonl                        # Robot execution logs
└── *.mp4                                     # Video recordings (if enabled)

logs/groot_server/                            # Server logs (in Isaac-GR00T/)
├── server_log_YYYY-MM-DD_HH-MM-SS.jsonl     # GR00T server logs
└── images/                                   # Input images seen by model
    ├── step_000001.png
    ├── step_000002.png
    └── ...
```

## Log Format

All logs use JSON Lines format (`.jsonl`) - one JSON object per line.

### Server Log (`server_log_*.jsonl`)

**Input entries:**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.789",
  "type": "input",
  "observation": {
    "video.rs_view": {
      "shape": [1, 480, 640, 3],
      "dtype": "uint8",
      "min": 0.0,
      "max": 255.0,
      "mean": 127.5,
      "std": 73.2,
      "data": [[[...]]]
    },
    "state.left_arm": {
      "shape": [1, 7],
      "dtype": "float64",
      "min": -1.2,
      "max": 1.5,
      "mean": 0.1,
      "std": 0.8,
      "data": [[0.1, 0.2, ...]]
    },
    ...
  }
}
```

**Output entries:**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.890",
  "type": "output",
  "inference_time": 0.123,
  "action": {
    "action.left_arm": {
      "shape": [16, 7],
      "dtype": "float32",
      "min": -0.5,
      "max": 0.8,
      "mean": 0.15,
      "std": 0.3,
      "data": [[...], [...], ...]
    },
    ...
  }
}
```

### Client Log (`client_actions.jsonl`)

**Observation sent:**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.780",
  "type": "observation_sent",
  "observation": {
    "video.rs_view": {"shape": [1, 480, 640, 3], ...},
    "state.left_arm": {"shape": [1, 7], ...},
    ...
  }
}
```

**Actions received:**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.900",
  "type": "actions_received",
  "actions": {
    "left_arm": [[...], [...], ...],   // 16 timesteps × 7 joints
    "right_arm": [[...], [...], ...],
    "left_hand": [[...], [...], ...],
    "right_hand": [[...], [...], ...]
  }
}
```

**Action returned (first action from sequence):**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.901",
  "type": "action_returned",
  "queue_index": 0,
  "action": [0.1, 0.2, ...]  // 28 DOF: left_arm(7) + right_arm(7) + left_hand(7) + right_hand(7)
}
```

**Cached action (subsequent timesteps):**
```json
{
  "step": 2,
  "timestamp": "2025-10-22T12:34:57.020",
  "type": "cached_action",
  "queue_index": 1,
  "action": [0.15, 0.25, ...]
}
```

### Robot State Log (`robot_states.jsonl`)

**Action injected:**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.902",
  "type": "action_to_robot",
  "action": [0.1, 0.2, ...]  // 28 DOF joint positions
}
```

**Actual robot state (after physics step):**
```json
{
  "step": 1,
  "timestamp": "2025-10-22T12:34:56.920",
  "type": "robot_actual_state",
  "joint_positions": {
    "left_arm": [0.09, 0.19, ...],   // 7 joints
    "right_arm": [0.11, 0.21, ...],  // 7 joints
    "left_hand": [0.08, 0.18, ...],  // 7 joints
    "right_hand": [0.12, 0.22, ...]  // 7 joints
  },
  "full_state": [0.0, 0.0, ..., 0.09, ...],  // All 43 DOF
  "reward": 0.5
}
```

## Usage

### Start GR00T Server with Logging

```bash
cd Isaac-GR00T
python scripts/inference_service_g1.py \
  --server \
  --model_path nvidia/GR00T-N1.5-3B \
  --embodiment_tag unitree_g1 \
  --data_config unitree_g1 \
  --log_dir logs/groot_server
```

### Run Simulation with Logging

```bash
cd g1_gr00t
python scripts/test_groot.py \
  --task G1-Move-Cylinder-Dex3-v0 \
  --groot_host localhost \
  --groot_port 5555 \
  --task_description "pick up the cylinder" \
  --video
```

Logs are automatically saved to `logs/YYYY-MM-DD_HH-MM-SS/TaskName/`.

## Analyzing Logs

### Load logs in Python:

```python
import json
from pathlib import Path

# Load client actions
log_dir = Path("logs/2025-10-22_12-34-56/G1-Move-Cylinder-Dex3-v0")

client_actions = []
with open(log_dir / "client_actions.jsonl") as f:
    for line in f:
        client_actions.append(json.loads(line))

robot_states = []
with open(log_dir / "robot_states.jsonl") as f:
    for line in f:
        robot_states.append(json.loads(line))

# Compare predicted vs actual
for i, (action_entry, state_entry) in enumerate(zip(client_actions, robot_states)):
    if action_entry['type'] == 'action_returned' and state_entry['type'] == 'robot_actual_state':
        predicted = action_entry['action']
        actual_left_arm = state_entry['joint_positions']['left_arm']
        print(f"Step {i}: Predicted {predicted[:7]}, Actual {actual_left_arm}")
```

### Verify trajectory following:

```python
import numpy as np

# Extract action sequence
action_steps = [e for e in robot_states if e['type'] == 'action_to_robot']
state_steps = [e for e in robot_states if e['type'] == 'robot_actual_state']

# Compare commanded vs actual positions
for action, state in zip(action_steps, state_steps):
    commanded = np.array(action['action'][:7])  # left arm
    actual = np.array(state['joint_positions']['left_arm'])
    error = np.linalg.norm(commanded - actual)
    print(f"Step {action['step']}: Position error = {error:.4f}")
```

## Key Features

1. **Full Data Chain**: Track data from model input → prediction → transmission → injection → execution
2. **Absolute Positions**: GR00T outputs absolute joint positions (not deltas)
3. **Timestamped**: Every entry has ISO timestamp for precise timing analysis
4. **Complete Data**: Full arrays included in logs for verification (not just statistics)
5. **Structured Format**: JSON Lines for easy parsing and analysis
6. **Image Saving**: Server saves all input images asynchronously (no performance impact)
   - Images saved as PNG files in `logs/groot_server/images/`
   - Named sequentially: `step_000001.png`, `step_000002.png`, etc.
   - Saved in background thread after response is sent to client
   - Fallback to numpy `.npy` format if PIL not available

## Joint Indexing

G1 Robot (43 DOF):
- Indices 0-6: Left leg (7 joints)
- Indices 7-13: Right leg (7 joints)
- Indices 14-16: Waist (3 joints)
- **Indices 17-23: Left arm (7 joints)** ← Controlled by GR00T
- **Indices 24-30: Left hand (7 joints)** ← Controlled by GR00T
- **Indices 31-37: Right arm (7 joints)** ← Controlled by GR00T
- **Indices 38-44: Right hand (7 joints)** ← Controlled by GR00T

GR00T Action Format (28 DOF):
- Indices 0-6: Left arm
- Indices 7-13: Right arm
- Indices 14-20: Left hand
- Indices 21-27: Right hand

