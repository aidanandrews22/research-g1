# NutPour Task Port Documentation

## Overview
This document tracks the port of the Isaac-NutPour-GR1T2-Pink-IK-Abs-v0 task from IsaacLab to g1_gr00t with GR00T N1 control.

## Key Differences Between Original and Ported Task

### Robot
- **Original**: GR1T2 (Fourier Intelligence robot)
- **Ported**: G1 with Dex3 hands (43 DOF)

### Control Method
- **Original**: Pink IK controller with OpenXR hand tracking
- **Ported**: GR00T N1.5 vision-language-action model

### Scene Objects (from IsaacLab nutpour_gr1t2_base_env_cfg.py)
1. **Table** - Static workspace surface
2. **SortingScale** - Target location for bowl
3. **SortingBowl** (yellow) - Container to be filled and placed
4. **SortingBeaker** (red) - Container to be discarded
5. **FactoryNut** (green) - Object to place in bowl
6. **BlackSortingBin** (blue) - Target location for beaker

### Task Goals
1. Pick up the sorting bowl with right hand
2. Place the sorting bowl on the sorting scale
3. Pick up the factory nut
4. Pour/place the factory nut into the sorting bowl
5. Pick up the sorting beaker with left hand
6. Place the sorting beaker into the black sorting bin

### Success Criteria (from terminations.py)
- Factory nut is in sorting bowl (within tolerance)
- Sorting bowl is on sorting scale (within tolerance)
- Sorting beaker is in sorting bin (within tolerance)

## File Structure

### g1_gr00t Task Structure
```
g1_gr00t/source/g1_gr00t/g1_gr00t/
├── tasks/
│   ├── __init__.py                    # Task registration
│   ├── move_cylinder/                 # Existing task (reference)
│   │   ├── __init__.py
│   │   ├── env_cfg.py
│   │   ├── gr00t_client.py
│   │   └── mdp/
│   │       ├── __init__.py
│   │       ├── observations.py
│   │       └── rewards.py
│   └── nutpour/                       # NEW TASK
│       ├── __init__.py
│       ├── env_cfg.py
│       ├── gr00t_client.py           # Reuse from move_cylinder
│       └── mdp/
│           ├── __init__.py
│           ├── observations.py       # Reuse observation functions
│           ├── rewards.py            # Placeholder
│           ├── terminations.py       # Port success conditions
│           └── events.py             # Port reset logic
├── scene/
│   ├── __init__.py
│   ├── cylinder_scene.py              # Existing scene
│   └── nutpour_scene.py              # NEW SCENE
└── config/
    ├── __init__.py
    ├── robot_config.py                # G1 Dex3 config
    └── camera_config.py               # Camera presets
```

### IsaacLab Source Files (Reference)
```
IsaacLab/source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/pick_place/
├── nutpour_gr1t2_base_env_cfg.py     # Scene + base configuration
├── nutpour_gr1t2_pink_ik_env_cfg.py  # Pink IK action config
└── mdp/
    ├── observations.py                # get_left_eef_pos, get_right_eef_pos, etc.
    ├── terminations.py                # task_done_nut_pour
    └── pick_place_events.py           # reset_object_poses_nut_pour
```

## Adaptation Strategy

### 1. Scene Configuration
- Copy object definitions from `nutpour_gr1t2_base_env_cfg.py::ObjectTableSceneCfg`
- Replace GR1T2 robot with G1 Dex3 configuration
- Adjust robot initial position to face the table
- Keep the same camera setup (robot_pov_cam)

### 2. Actions
- **Original**: Pink IK actions (14 arm joints, 22 hand joints)
- **Ported**: Direct joint position control via GR00T (28 DOF: 14 arm + 14 hand)

### 3. Observations
- Reuse existing observation functions from `g1_gr00t/observations/`
- Port any GR1T2-specific observations to G1 equivalents
- Keep image observations from cameras

### 4. MDP Functions
- **Terminations**: Port `task_done_nut_pour` from IsaacLab
- **Events**: Port `reset_object_poses_nut_pour` from IsaacLab
- **Rewards**: Placeholder (not used with GR00T)

### 5. GR00T Client
- Reuse existing `gr00t_client.py` from move_cylinder
- No changes needed - already supports multi-object manipulation

## Implementation Checklist

- [ ] Create nutpour task directory structure
- [ ] Create nutpour_scene.py with all objects
- [ ] Create env_cfg.py with NutPourEnvCfg
- [ ] Copy gr00t_client.py (or symlink)
- [ ] Create mdp functions (observations, terminations, events)
- [ ] Update tasks/__init__.py to register new task
- [ ] Update scene/__init__.py to export NutPourSceneCfg
- [ ] Test with test_groot.py

## Key Configuration Values

### Object Positions (from nutpour_gr1t2_base_env_cfg.py)
- Table: pos=[0.0, 0.55, 0.0]
- SortingScale: pos=[0.22236, 0.56, 0.9859]
- SortingBowl: pos=[0.02779, 0.43007, 0.9860]
- SortingBeaker: pos=[-0.13739, 0.45793, 0.9861]
- FactoryNut: pos=[-0.13739, 0.45793, 0.9995]
- BlackSortingBin: pos=[-0.32688, 0.46793, 0.98634]

### Robot Initial State (GR1T2 reference)
- Position: pos=(0, 0, 0.93)
- Rotation: rot=(0.7071, 0, 0, 0.7071)
- Arms in neutral reaching pose

### Success Tolerances (from terminations.py)
- Bowl to Scale: max_x=0.055, max_y=0.055, max_z=0.025
- Nut to Bowl: max_x=0.050, max_y=0.050, max_z=0.019
- Beaker to Bin: max_x=0.08, max_y=0.12, max_z=0.07

## Asset Paths
All assets are in ISAACLAB_NUCLEUS_DIR:
- Table: `Mimic/nut_pour_task/nut_pour_assets/table.usd`
- SortingScale: `Mimic/nut_pour_task/nut_pour_assets/sorting_scale.usd`
- SortingBowl: `Mimic/nut_pour_task/nut_pour_assets/sorting_bowl_yellow.usd`
- SortingBeaker: `Mimic/nut_pour_task/nut_pour_assets/sorting_beaker_red.usd`
- FactoryNut: `Mimic/nut_pour_task/nut_pour_assets/factory_m16_nut_green.usd`
- BlackSortingBin: `Mimic/nut_pour_task/nut_pour_assets/sorting_bin_blue.usd`


