# NutPour Task Port - Summary

## What Was Done

Successfully ported the Isaac-NutPour-GR1T2-Pink-IK-Abs-v0 task from IsaacLab to g1_gr00t with GR00T N1.5 control.

## Files Created

### Scene Configuration
- **`g1_gr00t/scene/nutpour_scene.py`** - Scene with table and all manipulation objects:
  - Table
  - Sorting Scale (target for bowl)
  - Sorting Bowl (yellow)
  - Sorting Beaker (red) 
  - Factory Nut (green)
  - Black Sorting Bin (target for beaker)

### Task Directory (`g1_gr00t/tasks/nutpour/`)
- **`__init__.py`** - Task registration (ID: `G1-NutPour-v0`)
- **`env_cfg.py`** - Environment configuration with G1 robot, cameras, actions, observations, terminations
- **`gr00t_client.py`** - Copied from move_cylinder (reusable)
- **`mdp/__init__.py`** - MDP module initialization
- **`mdp/observations.py`** - Reuses existing observation functions
- **`mdp/rewards.py`** - Placeholder reward function
- **`mdp/terminations.py`** - Ported `task_done_nut_pour` success conditions
- **`mdp/events.py`** - Ported `reset_object_poses_nut_pour` for randomization

### Updated Files
- **`g1_gr00t/scene/__init__.py`** - Added NutPourSceneCfg export
- **`g1_gr00t/tasks/__init__.py`** - Added nutpour task import
- **`scripts/list_envs.py`** - Fixed filter from "Template-" to "G1-"

## Task Details

### Robot Setup
- G1 with Dex3 hands (43 DOF total)
- Position: (0.0, 0.0, 0.93), facing table
- Base and legs locked (fix_root_link=True)
- Arms and hands controllable (28 DOF)

### Task Goals
1. Pick up sorting bowl with right hand
2. Place sorting bowl on sorting scale
3. Pick up factory nut
4. Pour/place factory nut into sorting bowl
5. Pick up sorting beaker with left hand
6. Place sorting beaker into black sorting bin

### Success Criteria
All three conditions must be met:
- Factory nut in sorting bowl (tolerance: x=0.05m, y=0.05m, z=0.019m)
- Sorting bowl on sorting scale (tolerance: x=0.055m, y=0.055m, z=0.025m)
- Sorting beaker in black bin (tolerance: x=0.08m, y=0.12m, z=0.07m)

### Failure Conditions
- Time out (20 seconds)
- Any object drops below 0.5m height

## How to Run

```bash
# Activate environment
conda activate g1

# List available environments (verify registration)
python scripts/list_envs.py

# Run with GR00T control
python scripts/test_groot.py \
  --task G1-NutPour-v0 \
  --task_description "sort the objects: place bowl on scale with nut inside, put beaker in bin" \
  --num_envs 1 \
  --video \
  --video_length 500 \
  --device cuda:1
```

## Modular Structure

The implementation follows the same structure as `move_cylinder`:
- Reusable `gr00t_client.py` (works for any task)
- Shared observation functions from `g1_gr00t.observations`
- Standard IsaacLab MDP structure
- Minimal dependencies on task-specific code

To add a new task, simply:
1. Create scene config in `g1_gr00t/scene/`
2. Create task directory in `g1_gr00t/tasks/`
3. Define env_cfg.py with scene + robot + MDP
4. Register in task's `__init__.py`
5. Import in `g1_gr00t/tasks/__init__.py`

## Key Differences from IsaacLab Original

| Aspect | IsaacLab Original | g1_gr00t Port |
|--------|-------------------|---------------|
| Robot | GR1T2 (Fourier) | G1 with Dex3 hands |
| Control | Pink IK + OpenXR hand tracking | GR00T N1.5 VLA model |
| Action Space | Pose-based IK (7 DoF arms + 22 hand) | Joint position (28 DoF) |
| Input | Hand tracking from OpenXR | Vision + state from cameras |
| Hand Joints | 22 DoF (11 per hand) | 14 DoF (7 per hand, Dex3) |

## Asset Paths

All assets loaded from `ISAACLAB_NUCLEUS_DIR/Mimic/nut_pour_task/nut_pour_assets/`:
- `table.usd` (scale: 1.0, 1.0, 1.3)
- `sorting_scale.usd`
- `sorting_bowl_yellow.usd` (scale: 1.0, 1.0, 1.5)
- `sorting_beaker_red.usd` (scale: 0.45, 0.45, 1.3)
- `factory_m16_nut_green.usd` (scale: 0.5, 0.5, 0.5)
- `sorting_bin_blue.usd` (scale: 0.75, 1.0, 1.0)

## Verification Status

✅ Task registered and visible in `list_envs.py`
✅ Scene configuration created
✅ Environment configuration created
✅ MDP functions ported
✅ Task module initialized
⏳ Pending: Full runtime test with GR00T server


