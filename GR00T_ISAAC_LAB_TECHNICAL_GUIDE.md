# GR00T + Isaac Lab Integration - Technical Guide

## System Overview

This document describes the integration of NVIDIA's GR00T-N1.5-3B vision-language-action model with Isaac Lab for humanoid robot control (Unitree G1).

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Isaac Lab Simulation (g1_gr00t)                            │
│  - G1 Robot (43 DOF: 29 body + 14 hand)                    │
│  - Physics @ 120Hz, Control @ 60Hz (decimation=2)          │
│  - Camera sensors (RGB: 640x480x3)                          │
└──────────────┬──────────────────────────────────────────────┘
               │ ZMQ Request/Reply
               │ (msgpack serialization)
               ↓
┌─────────────────────────────────────────────────────────────┐
│  GR00T Inference Server (Isaac-GR00T)                       │
│  - Model: GR00T-N1.5-3B (finetuned for G1)                 │
│  - Embodiment: "new_embodiment"                             │
│  - Action horizon: 16 timesteps                             │
│  - Denoising steps: 4                                       │
└─────────────────────────────────────────────────────────────┘
```

## Robot Configuration

### DOF Breakdown (43 Total)
- **Legs**: 12 DOF (6 per leg) - LOCKED in simulation
- **Waist**: 3 DOF (yaw, roll, pitch) - LOCKED in simulation  
- **Arms**: 14 DOF (7 per arm)
  - shoulder_pitch, shoulder_roll, shoulder_yaw
  - elbow
  - wrist_yaw, wrist_roll, wrist_pitch
- **Hands**: 14 DOF (7 per hand, Dex3 configuration)
  - hand_index_0/1, hand_middle_0/1, hand_thumb_0/1/2

### Controlled DOF: 28
Only arms (14) and hands (14) are actively controlled by GR00T. Legs and waist are locked with high stiffness (10000.0) to prevent movement.

### Joint Ranges (Arms)
From training data statistics:
```
Left arm:
  min: [-1.073,  0.190, -0.523, -1.047, -0.938, -1.614, -0.935]
  max: [ 0.684,  0.840,  0.941,  1.314,  1.541,  1.008,  0.656]
```

All values in radians. These are absolute joint positions, not velocities or deltas.

## Data Flow

### 1. Observation Collection (Isaac Lab → Client)

**Source:** `g1_gr00t/tasks/*/env_cfg.py`

Isaac Lab provides observations through two terms:
- `robot_body_state`: Returns (87,) array
- `robot_hand_state`: Returns (42,) array

**Critical Format Detail:** These arrays are **BLOCK CONCATENATED**, not interleaved:
```python
body_state = [
    pos_0, pos_1, ..., pos_28,      # Indices 0-28: All positions
    vel_0, vel_1, ..., vel_28,      # Indices 29-57: All velocities
    torque_0, ..., torque_28        # Indices 58-86: All torques
]

hand_state = [
    pos_0, ..., pos_13,             # Indices 0-13: All positions
    vel_0, ..., vel_13,             # Indices 14-27: All velocities
    torque_0, ..., torque_13        # Indices 28-41: All torques
]
```

**Extraction (CORRECTED):**
```python
# CORRECT way to extract positions:
body_positions = body_state[:29]    # First 29 elements
hand_positions = hand_state[:14]    # First 14 elements

# WRONG way (was causing bugs):
# body_positions = body_state[::3]  # Takes every 3rd element - mixes pos/vel/torque!
```

### 2. Observation Preprocessing (Client)

**Source:** `g1_gr00t/tasks/*/gr00t_client.py`

The client transforms Isaac Lab observations into GR00T format:

```python
full_state = np.concatenate([body_positions, hand_positions])  # 43 DOF

# Extract arm and hand states (indices based on robot structure)
left_arm = full_state[15:22]   # 7 joints
right_arm = full_state[29:36]  # 7 joints
left_hand = full_state[22:29]  # 7 joints
right_hand = full_state[36:43] # 7 joints
```

**GR00T Input Format:**
```python
{
    "video.rs_view": np.ndarray,         # (1, H, W, 3) uint8, range [0, 255]
    "state.left_arm": np.ndarray,        # (1, 7) float64, in radians
    "state.right_arm": np.ndarray,       # (1, 7) float64, in radians
    "state.left_hand": np.ndarray,       # (1, 7) float64, in radians
    "state.right_hand": np.ndarray,      # (1, 7) float64, in radians
    "annotation.human.task_description": ["text string"]
}
```

**Real Example (Step 1):**
```json
{
  "video.rs_view": {
    "shape": [1, 480, 640, 3],
    "dtype": "uint8",
    "min": 0.0,
    "max": 244.0
  },
  "state.left_arm": {
    "shape": [1, 7],
    "data": [[0.0193, 0.0184, -0.0244, -0.1116, -0.1169, 0.1359, 0.0367]]
  },
  "state.right_arm": {
    "shape": [1, 7],
    "data": [[0.0045, -0.0110, -0.0001, -0.0020, 0.0015, -0.0364, -0.0001]]
  }
}
```

### 3. Server Processing (GR00T Model)

**Source:** `Isaac-GR00T/scripts/inference_service_g1.py`

The server receives the observation and runs inference:

**Transform Pipeline:**
1. `VideoToTensor` → Convert image to tensor
2. `VideoCrop` → Crop with scale=0.95
3. `VideoResize` → Resize to 224x224
4. `VideoColorJitter` → Data augmentation (training only)
5. `VideoToNumpy` → Back to numpy
6. `StateActionToTensor` → Convert states to tensors
7. `StateActionTransform` → **Normalize states** using min-max
8. `ConcatTransform` → Concatenate state modalities
9. `GR00TTransform` → Model-specific preprocessing
10. **Model Inference** → GR00T-N1.5-3B forward pass
11. `GR00TTransform.unapply()` → Split concatenated outputs
12. `ConcatTransform.unapply()` → Split into individual keys
13. `StateActionTransform.unapply()` → **Denormalize actions** using min-max
14. `StateActionToTensor.unapply()` → Convert back to numpy

**Normalization/Denormalization:**
```python
# Forward (normalize): action ∈ [min, max] → normalized ∈ [-1, 1]
normalized = 2 * (action - min) / (max - min) - 1

# Inverse (denormalize): normalized ∈ [-1, 1] → action ∈ [min, max]
action = (normalized + 1) / 2 * (max - min) + min
```

**Model Output Format:**
```python
{
    "action.left_arm": np.ndarray,     # (16, 7) float32
    "action.right_arm": np.ndarray,    # (16, 7) float32
    "action.left_hand": np.ndarray,    # (16, 7) float32
    "action.right_hand": np.ndarray    # (16, 7) float32
}
```

**Real Example (Step 1):**
```json
{
  "action.left_arm": {
    "shape": [16, 7],
    "dtype": "float32",
    "min": -0.267,
    "max": 0.283,
    "first_timestep": [-0.142, 0.210, 0.038, -0.215, 0.022, -0.016, 0.012]
  },
  "action.right_arm": {
    "shape": [16, 7],
    "first_timestep": [-0.219, -0.198, -0.031, -0.045, -0.081, -0.088, 0.119]
  }
}
```

These are **absolute joint positions** in radians, denormalized and ready to use.

### 4. Action Queue Management (Client)

**Source:** `g1_gr00t/tasks/*/gr00t_client.py`

The client receives 16 timesteps of actions but applies them one at a time:

```python
# Received from server: 16 timesteps
left_arm_actions = response['action.left_arm']    # (16, 7)
right_arm_actions = response['action.right_arm']  # (16, 7)
left_hand_actions = response['action.left_hand']  # (16, 7)
right_hand_actions = response['action.right_hand'] # (16, 7)

# Reconstruct 28 DOF actions (arms + hands only, no legs/waist)
for t in range(16):
    action_28dof = np.concatenate([
        left_arm_actions[t],    # 7 DOF
        right_arm_actions[t],   # 7 DOF
        left_hand_actions[t],   # 7 DOF
        right_hand_actions[t],  # 7 DOF
    ])
    self._action_queue.append(action_28dof)

# Return first action, queue the rest
return torch.from_numpy(self._action_queue[0]).float()
```

**Subsequent steps** use cached actions from the queue until all 16 are consumed, then query GR00T again.

**Real Example (Step 1):**
```json
{
  "action": [
    -0.1507, 0.2108, 0.0326, -0.2118, -0.0004, -0.0033, 0.0103,  // left_arm (7)
    -0.2187, -0.1977, -0.0309, -0.0454, -0.0806, -0.0875, 0.1189, // right_arm (7)
    -0.0100, -0.0223, -0.0126, -0.0188, 0.0000, 0.0346, 0.0230,   // left_hand (7)
    -0.0008, 0.0006, 0.0025, 0.0042, 0.0000, 0.0068, 0.0007       // right_hand (7)
  ]
}
```

### 5. Action Application (Isaac Lab)

**Source:** `g1_gr00t/tasks/*/env_cfg.py`

**CRITICAL CONFIGURATION:**
```python
joint_pos = base_mdp.JointPositionActionCfg(
    asset_name="robot",
    joint_names=[...],  # 28 joints (arms + hands)
    scale=1.0,
    use_default_offset=False,  # MUST be False for absolute positions!
)
```

**Why `use_default_offset=False` is Critical:**
- `True`: Treats actions as **offsets** → `target = default_pos + action`
- `False`: Treats actions as **absolute positions** → `target = action`

GR00T outputs absolute positions, so we must use `False`.

**Action Execution:**
The environment applies position control with:
- **Stiffness**: 50-100 (arms), 100 (hands)
- **Damping**: 2.0 (arms), 10.0 (hands)
- **Control frequency**: 60Hz (simulation at 120Hz with decimation=2)

**Real Example (Step 1 → Step 2):**
```json
// Step 1
{
  "commanded": {
    "left_arm": [-0.151, 0.211, 0.033, -0.212, -0.000, -0.003, 0.010]
  },
  "actual_after_physics": {
    "left_arm": [1.225, -4.616, 0.413, 0.815, 2.711, -0.036, -0.000]
  }
}

// Note: Large discrepancy indicates the controller is still converging
// or there are external forces/constraints affecting the robot
```

## Communication Protocol

### ZMQ Request-Reply Pattern

**Serialization:** msgpack with custom handlers for numpy arrays

**Request Format:**
```python
{
    "endpoint": "get_action",
    "data": {
        "video.rs_view": np.ndarray,
        "state.left_arm": np.ndarray,
        # ... other modalities
    }
}
```

**Response Format:**
```python
{
    "action.left_arm": np.ndarray,    # (16, 7)
    "action.right_arm": np.ndarray,   # (16, 7)
    "action.left_hand": np.ndarray,   # (16, 7)
    "action.right_hand": np.ndarray   # (16, 7)
}
```

**Timing:**
- Request latency: ~50-100ms (includes image encoding, network, inference)
- Inference time: ~30-50ms on GPU
- Queue allows amortizing cost over 16 steps

## Model Configuration

### Embodiment: `new_embodiment`

**Modality Configuration:**
```json
{
  "video": {
    "delta_indices": [0],
    "modality_keys": ["video.rs_view"]
  },
  "state": {
    "delta_indices": [0],
    "modality_keys": ["state.left_arm", "state.right_arm", "state.left_hand", "state.right_hand"]
  },
  "action": {
    "delta_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    "modality_keys": ["action.left_arm", "action.right_arm", "action.left_hand", "action.right_hand"]
  },
  "language": {
    "delta_indices": [0],
    "modality_keys": ["annotation.human.task_description"]
  }
}
```

**State Metadata:**
```json
{
  "left_arm": {
    "absolute": true,
    "rotation_type": null,
    "shape": [7],
    "continuous": true
  }
  // Similar for right_arm, left_hand, right_hand
}
```

**Action Metadata:**
```json
{
  "left_arm": {
    "absolute": true,      // Actions are absolute positions, not deltas
    "rotation_type": null, // No special rotation representation
    "shape": [7],
    "continuous": true
  }
}
```

**Action Statistics (for normalization):**
```json
{
  "left_arm": {
    "min": [-1.073, 0.190, -0.523, -1.047, -0.938, -1.614, -0.935],
    "max": [0.684, 0.840, 0.941, 1.314, 1.541, 1.008, 0.656],
    "mean": [-0.076, 0.309, 0.255, -0.449, -0.089, 0.048, -0.170]
  }
}
```

### Model Architecture

- **Backbone**: EAGLE2 Vision-Language Model
- **Action Head**: Flow Matching Diffusion Model
- **Parameters**: ~3B total
  - Vision tower: ~2.2B (tuned)
  - LLM: ~800M (frozen)
  - Action head: ~550M DiT + 200M projector (tuned)

**Inference Configuration:**
- Denoising steps: 4
- Action horizon: 16 timesteps
- Input resolution: 224x224 (resized from 640x480)
- Compute dtype: bfloat16

## Logging System

### Server Logs
**Location:** `Isaac-GR00T/logs/groot_server/server_log_TIMESTAMP.jsonl`

Each inference step logs:
```json
{
  "step": 1,
  "timestamp": "2025-10-22T03:40:04.539062",
  "type": "input",
  "observation": {
    "video.rs_view": {"shape": [1, 480, 640, 3], "min": 0, "max": 244, ...},
    "state.left_arm": {"data": [[...]], ...}
  }
}
{
  "step": 1,
  "timestamp": "2025-10-22T03:40:04.592341",
  "type": "output",
  "inference_time": 0.053,
  "action": {
    "action.left_arm": {"shape": [16, 7], "min": -0.267, "max": 0.283, ...}
  }
}
```

**Images:** Saved to `logs/groot_server/images/step_NNNNNN.png`

### Client Logs
**Location:** `g1_gr00t/logs/TIMESTAMP/TASK/client_actions.jsonl`

Logs three events per query:
1. `observation_sent`: What was sent to server
2. `actions_received`: What was received from server (16 timesteps)
3. `action_returned`: What was returned to simulation (1 timestep)

Plus cached action usage:
4. `cached_action`: When using queued actions (steps 2-16)

### Robot State Logs
**Location:** `g1_gr00t/logs/TIMESTAMP/TASK/robot_states.jsonl`

Logs two events per step:
1. `action_to_robot`: The 28 DOF command sent
2. `robot_actual_state`: The 43 DOF state after physics, including:
   - Joint positions for all parts
   - Reward value
   - Full 43 DOF state vector

## Common Issues & Solutions

### Issue 1: Robot Makes Wild Movements
**Cause:** Observations were extracted incorrectly using `[::3]` instead of `[:29]`  
**Effect:** Sends velocities/torques as positions → Model gets garbage input  
**Solution:** Use `body_state[:29]` and `hand_state[:14]`

### Issue 2: Robot Doesn't Reach Commanded Positions
**Cause:** `use_default_offset=True` treats absolute positions as offsets  
**Effect:** `target = default + action` instead of `target = action`  
**Solution:** Set `use_default_offset=False`

### Issue 3: Actions Seem "Normalized"
**Explanation:** GR00T predictions can be small values like [-0.3, 0.3] even after denormalization. This is normal - the model learned to predict positions in the training data range, which happens to be small for some joints.

**Verification:** Check that values are within training statistics min/max range.

### Issue 4: Different Outputs on Same Inputs
**Explanation:** The model is **deterministic** given the same inputs. Different outputs mean:
- Different camera images (most likely)
- Different joint states
- Different random seeds (if using stochastic sampling)

## Performance Metrics

### Model Evaluation
On test dataset (g1-pick-apple):
- **Action MSE**: 0.001067
- This indicates the model accurately predicts actions matching ground truth demonstrations

### Runtime Performance
- **Inference latency**: ~50ms per query
- **Action horizon**: 16 steps
- **Amortized cost**: ~3ms per simulation step
- **GPU memory**: ~6GB (model + activations)

## File Structure

```
g1/
├── Isaac-GR00T/              # GR00T model and server
│   ├── gr00t/
│   │   ├── model/            # Model architecture
│   │   ├── data/             # Data transforms
│   │   └── eval/             # Inference clients/servers
│   ├── scripts/
│   │   └── inference_service_g1.py  # Server implementation
│   └── logs/groot_server/    # Server logs
│
└── g1_gr00t/                 # Isaac Lab simulation
    ├── source/g1_gr00t/
    │   ├── config/           # Robot configuration
    │   ├── tasks/            # Task environments
    │   │   ├── nutpour/
    │   │   │   ├── env_cfg.py        # Environment config
    │   │   │   └── gr00t_client.py   # GR00T client
    │   │   └── move_cylinder/
    │   └── observations/     # Observation functions
    ├── scripts/
    │   └── test_groot.py     # Test script
    └── logs/                 # Simulation logs
```

## Quick Reference

### Starting the Server
```bash
cd Isaac-GR00T
CUDA_VISIBLE_DEVICES=1 python scripts/inference_service_g1.py \
  --server \
  --model-path /path/to/unitree-g1-finetune/ \
  --data-config unitree_g1 \
  --embodiment-tag new_embodiment \
  --denoising-steps 4
```

### Running the Simulation
```bash
cd g1_gr00t
python scripts/test_groot.py \
  --task G1-NutPour-v0 \
  --video \
  --video_length 500 \
  --groot_host localhost \
  --groot_port 5555
```

### Data Types Quick Reference
- **Joint positions**: float, radians, absolute
- **Images**: uint8, [0-255], RGB
- **Actions**: float32, radians, absolute positions
- **Batch dimension**: Always present, usually size 1
- **Time dimension**: State=1, Action=16

---

*Document Version: 1.0*  
*Last Updated: 2025-10-22*  
*For questions, refer to the codebase or contact the development team.*

