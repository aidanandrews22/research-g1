# Logging Implementation Summary

## Changes Made

### 1. Server-Side Logging (`Isaac-GR00T/scripts/inference_service_g1.py`)

**Added:**
- `ImageSaver` class for async image saving
  - Background thread with queue
  - Saves images as PNG (or numpy if PIL unavailable)
  - No performance impact (saves after response sent)
- `LoggingPolicyWrapper` class that wraps the GR00T policy
- Logs all inputs and outputs with full data arrays
- Records inference timing
- Saves to `logs/groot_server/server_log_TIMESTAMP.jsonl`
- Saves input images to `logs/groot_server/images/step_NNNNNN.png`

**Modified:**
- Added `log_dir` argument to `ArgsConfig`
- Wrapped policy with `LoggingPolicyWrapper` before passing to server
- Imports: `json`, `Path`, `datetime`, `threading`, `Queue`

### 2. Client-Side Logging (`g1_gr00t/source/g1_gr00t/g1_gr00t/tasks/*/gr00t_client.py`)

**Modified both:**
- `g1_gr00t/tasks/nutpour/gr00t_client.py`
- `g1_gr00t/tasks/move_cylinder/gr00t_client.py`

**Added:**
- `log_dir` parameter to `__init__` and `create_groot_client`
- `log_file` and `_step_count` instance variables
- Logging for:
  - Observations sent to server
  - Actions received from server
  - Actions returned to simulation
  - Cached actions from queue
- Saves to `LOG_DIR/client_actions.jsonl`

**Imports added:**
- `json`, `Path`, `datetime`

### 3. Simulation Logging (`g1_gr00t/scripts/test_groot.py`)

**Added:**
- Output directory creation at start: `logs/TIMESTAMP/TASK/`
- Pass `log_dir` to `create_groot_client()`
- Logging for:
  - Actions sent to robot (before injection)
  - Actual robot joint positions (after physics step)
  - Full 43 DOF state
  - Per-joint positions for arms and hands
  - Reward values
- Saves to `OUTPUT_DIR/robot_states.jsonl`
- Videos also save to same `OUTPUT_DIR`

**Modified:**
- Import `json`
- Create output directory before client creation
- Added robot state logging after each step
- Unified output directory for logs and videos

## Data Flow with Logging

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SIMULATION (test_groot.py)                                   │
│    - Observation from Isaac Lab                                 │
│    └─> Send to client                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CLIENT (gr00t_client.py)                                     │
│    - Convert observation to GR00T format                        │
│    - LOG: observation_sent → client_actions.jsonl              │
│    └─> Send to server via ZMQ                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. SERVER (inference_service_g1.py + LoggingPolicyWrapper)     │
│    - LOG: input → server_log_*.jsonl                           │
│    - Run GR00T model inference                                  │
│    - LOG: output → server_log_*.jsonl                          │
│    └─> Return actions via ZMQ                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. CLIENT (gr00t_client.py)                                     │
│    - Receive 16 timesteps of actions                            │
│    - LOG: actions_received → client_actions.jsonl              │
│    - Convert to 28 DOF format                                   │
│    - LOG: action_returned → client_actions.jsonl               │
│    └─> Return first action                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. SIMULATION (test_groot.py)                                   │
│    - LOG: action_to_robot → robot_states.jsonl                 │
│    - Inject action into robot                                   │
│    - Step physics simulation                                    │
│    - LOG: robot_actual_state → robot_states.jsonl              │
└─────────────────────────────────────────────────────────────────┘
```

## Verification Workflow

### 1. Compare Model Output to Client Reception
```python
# server_log_*.jsonl: output entries
# client_actions.jsonl: actions_received entries
# Should be identical (verify no corruption in ZMQ transmission)
```

### 2. Compare Client Actions to Robot Commands
```python
# client_actions.jsonl: action_returned entries
# robot_states.jsonl: action_to_robot entries
# Should be identical (verify no transformation issues)
```

### 3. Compare Robot Commands to Actual State
```python
# robot_states.jsonl: action_to_robot vs robot_actual_state
# Should be close (small error from physics/control)
# This verifies trajectory following accuracy
```

## Example Usage

### Start Server
```bash
cd Isaac-GR00T
python scripts/inference_service_g1.py \
  --server \
  --model_path nvidia/GR00T-N1.5-3B \
  --embodiment_tag unitree_g1 \
  --data_config unitree_g1 \
  --log_dir logs/groot_server
```

### Run Simulation
```bash
cd g1_gr00t
python scripts/test_groot.py \
  --task G1-Move-Cylinder-Dex3-v0 \
  --video \
  --video_length 500
```

### Check Logs
```bash
# Simulation logs
ls -lh logs/2025-10-22_*/G1-Move-Cylinder-Dex3-v0/

# Server logs (if using default log_dir)
cd ../Isaac-GR00T
ls -lh logs/groot_server/
```

## Notes

- **Absolute positions**: GR00T outputs absolute joint positions, not deltas
- **Full data**: Complete arrays logged for verification
- **Timestamped**: All entries have ISO timestamps
- **Per-step**: Logging happens every simulation step
- **Shared directory**: Logs and videos in same timestamped directory
- **JSON Lines**: Easy to parse line-by-line for large files

## File Locations

- Server: `Isaac-GR00T/scripts/inference_service_g1.py`
- Client (nutpour): `g1_gr00t/source/g1_gr00t/g1_gr00t/tasks/nutpour/gr00t_client.py`
- Client (move_cylinder): `g1_gr00t/source/g1_gr00t/g1_gr00t/tasks/move_cylinder/gr00t_client.py`
- Simulation: `g1_gr00t/scripts/test_groot.py`
- Documentation: `LOGGING.md`

