# G1 GR00T Isaac Lab Environment Setup

## Overview

This project sets up a standalone Isaac Lab environment for G1 robot (43 DOF Dex3) cylinder manipulation, ready for GR00T N1.5 policy integration.

## Project Structure

```
g1_gr00t/
├── assets/                               # Robot and scene USD files
│   ├── robots/
│   │   └── g1-29dof_wholebody_dex3/     # G1 robot with Dex3 hands
│   └── objects/
│       ├── small_warehouse/              # Warehouse environment
│       ├── PackingTable/                 # Scene objects
│       └── PackingTable_2/
├── source/g1_gr00t/g1_gr00t/
│   ├── config/
│   │   ├── robot_config.py              # G1 43DOF configuration
│   │   └── camera_config.py             # Camera presets
│   ├── observations/
│   │   ├── g1_state.py                  # Body joints (29 DOF)
│   │   ├── dex3_state.py                # Hand joints (14 DOF)
│   │   └── camera_obs.py                # Camera images
│   ├── scene/
│   │   └── cylinder_scene.py            # Scene with warehouse, tables, cylinder
│   └── tasks/
│       └── move_cylinder/
│           ├── env_cfg.py               # Environment configuration
│           ├── gr00t_client.py          # GR00T integration placeholder
│           └── mdp/
│               ├── observations.py      # Observation functions
│               └── rewards.py           # Reward functions
└── scripts/
    └── zero_agent.py                    # Test script (adapted)
```

## Robot Configuration

- **43 DOF Total:**
  - 12 leg joints (6 per leg)
  - 3 waist joints
  - 14 arm joints (7 per arm)
  - 14 hand joints (7 per Dex3 hand)

- **Joint names match GR00T dataset exactly** (verified against `Isaac-GR00T/datasets/g1-pick-apple/meta/info.json`)

## Observations

The environment provides separate observations (not concatenated):

1. **robot_body_state** `[batch, 87]`:
   - 29 joint positions
   - 29 joint velocities
   - 29 joint torques

2. **robot_hand_state** `[batch, 42]`:
   - 14 joint positions
   - 14 joint velocities
   - 14 joint torques

3. **camera_images** `Dict[str, Tensor]`:
   - `front_camera`: Front-facing head camera
   - `left_wrist_camera`: Left Dex3 wrist camera
   - `right_wrist_camera`: Right Dex3 wrist camera
   - `robot_camera`: Third-person view

## Actions

- Direct joint position control for all 43 joints
- Action space: `[batch, 43]` joint positions

## Installation

1. Ensure Isaac Lab is installed (conda environment recommended)

2. Install this package in editable mode:
```bash
cd g1_gr00t
python -m pip install -e source/g1_gr00t
```

## Running the Environment

### Test with Zero Actions

```bash
cd g1_gr00t
python scripts/zero_agent.py --task G1-Move-Cylinder-Dex3-v0 --num_envs 1
```

Or simply:
```bash
python scripts/zero_agent.py  # Defaults to G1-Move-Cylinder-Dex3-v0
```

### Expected Behavior

The environment should:
1. Load with warehouse scene, two tables, and cylinder object
2. Spawn G1 robot at specified position
3. Display observation shapes:
   - Body state: (1, 87)
   - Hand state: (1, 42)
   - Camera images: Dict with 4 cameras
4. Accept 43-dim action inputs
5. Run stably with zero actions

## GR00T Integration

To integrate GR00T N1.5 policy:

1. **Implement `gr00t_client.py`:**
   - Connect to GR00T server
   - Format observations (joint states + images)
   - Query policy for actions
   - Handle multi-step predictions

2. **Update test script:**
```python
from g1_gr00t.tasks.move_cylinder.gr00t_client import create_groot_client

groot_client = create_groot_client(server_url="http://localhost:8000")

# In simulation loop:
# actions = groot_client.query_policy(obs)
```

3. **Observation format for GR00T:**
   - Body: 29 joints (legs + waist + arms)
   - Hands: 14 joints (Dex3 configuration)
   - Cameras: RGB images from 4 viewpoints

## Key Features

- **No DDS/teleoperation code**: Clean Isaac Lab-only implementation
- **Modular structure**: Easy to maintain and extend
- **Standard interfaces**: Uses Isaac Lab built-in managers
- **Single integration point**: Only `gr00t_client.py` needs implementation
- **Matches GR00T dataset**: 43 DOF with identical joint names

## Troubleshooting

### Missing USD Files

If robot or scene assets are missing:
```bash
# Verify assets were copied
ls -la g1_gr00t/assets/robots/g1-29dof_wholebody_dex3/
ls -la g1_gr00t/assets/objects/
```

### Import Errors

Ensure package is installed:
```bash
pip list | grep g1-gr00t
```

Reinstall if needed:
```bash
cd g1_gr00t
python -m pip install -e source/g1_gr00t --force-reinstall
```

### Environment Not Found

Check gym registration:
```python
import gymnasium as gym
import g1_gr00t.tasks
print("G1-Move-Cylinder-Dex3-v0" in gym.envs.registry.keys())
```

## Next Steps

1. ✅ Base environment setup complete
2. ⏭️ Test environment with zero actions
3. ⏭️ Implement GR00T client connection
4. ⏭️ Query GR00T policy for actions
5. ⏭️ Deploy and validate with real GR00T N1.5 model

