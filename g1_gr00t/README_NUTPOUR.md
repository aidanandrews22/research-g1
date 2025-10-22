# G1 NutPour Task with GR00T N1.5

This task implements a complex bi-manual manipulation scenario where the G1 robot sorts objects on a table.

## Task Description

The robot must:
1. **Pick up the yellow sorting bowl** (right hand)
2. **Place the bowl on the sorting scale** 
3. **Pick up the green factory nut**
4. **Place/pour the nut into the bowl**
5. **Pick up the red sorting beaker** (left hand)
6. **Place the beaker into the blue sorting bin**

## Quick Start

### 1. Basic Environment Test (No GR00T Required)

Test that the environment loads correctly:

```bash
conda activate g1
python scripts/test_env_basic.py --task G1-NutPour-v0 --device cuda:1
```

This will:
- Create the environment
- Reset it
- Run 10 random action steps
- Verify everything works

### 2. Run with GR00T Control

**Prerequisites:**
- GR00T N1.5 server running on `localhost:5555` (or specify with `--groot_host` and `--groot_port`)

```bash
conda activate g1

# Run with GR00T policy
python scripts/test_groot.py \
  --task G1-NutPour-v0 \
  --task_description "sort the objects on the table" \
  --num_envs 1 \
  --video \
  --video_length 500 \
  --device cuda:1
```

**Custom task descriptions you can try:**
- `"sort the objects on the table"`
- `"place the bowl on the scale with the nut inside, put the beaker in the bin"`
- `"organize the workspace: bowl goes to scale, nut goes in bowl, beaker goes to bin"`

### 3. Verify Task Registration

List all available tasks:

```bash
python scripts/list_envs.py
```

You should see:
- `G1-Move-Cylinder-Dex3-v0` (original task)
- `G1-NutPour-v0` (new task)

## Environment Details

### Scene Objects

| Object | Color | Purpose | Initial Position |
|--------|-------|---------|------------------|
| Table | Gray | Workspace | (0.0, 0.55, 0.0) |
| Sorting Scale | Metal | Target for bowl | (0.22, 0.56, 0.99) |
| Sorting Bowl | Yellow | Container for nut | (0.03, 0.43, 0.99) |
| Factory Nut | Green | Small object to sort | (-0.14, 0.46, 1.00) |
| Sorting Beaker | Red | Container to discard | (-0.14, 0.46, 0.99) |
| Sorting Bin | Blue | Target for beaker | (-0.33, 0.47, 0.99) |

### Robot Configuration

- **Model**: G1 with Dex3 hands
- **Total DOF**: 43 (12 legs + 3 waist + 14 arms + 14 hands)
- **Controlled DOF**: 28 (14 arms + 14 hands)
- **Fixed**: Base, legs, waist (standing pose)
- **Position**: (0.0, 0.0, 0.93)
- **Orientation**: Facing table (90° rotation)

### Action Space

28-dimensional continuous action space:
- 14 arm joints: left/right shoulder (pitch/roll/yaw), elbow, wrist (yaw/roll/pitch)
- 14 hand joints: Dex3 configuration (7 per hand)

### Observation Space

- `robot_body_state`: Body joint states (87 values: 29 joints × 3)
- `robot_hand_state`: Hand joint states (42 values: 14 joints × 3)
- `camera_images`: RGB images from 4 cameras
  - `front_camera`: Front-facing camera
  - `left_wrist_camera`: Left wrist camera
  - `right_wrist_camera`: Right wrist camera
  - `robot_camera`: World view camera

### Success Conditions

Episode succeeds when ALL three conditions are met:

1. **Nut in Bowl**: 
   - Distance < 0.05m (x, y)
   - Height difference < 0.019m (z)

2. **Bowl on Scale**:
   - Distance < 0.055m (x, y)
   - Height difference < 0.025m (z)

3. **Beaker in Bin**:
   - Distance < 0.08m (x), < 0.12m (y)
   - Height difference < 0.07m (z)

### Failure Conditions

Episode terminates early if:
- Any object drops below 0.5m height
- Time limit reached (20 seconds = 400 steps at 5x decimation)

## Video Recording

Videos are saved to `videos/YYYY-MM-DD_HH-MM-SS/G1-NutPour-v0/`:
- `front_camera.mp4`
- `left_wrist_camera.mp4`
- `right_wrist_camera.mp4`
- `robot_camera.mp4`

Each video is H.264 encoded at 50 FPS.

## Command Line Options

```bash
python scripts/test_groot.py --help
```

Key options:
- `--task`: Task name (default: `G1-Move-Cylinder-Dex3-v0`)
- `--task_description`: Natural language task description for GR00T
- `--num_envs`: Number of parallel environments (default: 1)
- `--groot_host`: GR00T server hostname (default: `localhost`)
- `--groot_port`: GR00T server port (default: 5555)
- `--video`: Enable video recording
- `--video_length`: Number of steps to record (default: 500)
- `--device`: Compute device (default: `cuda:0`)

## Troubleshooting

### Environment doesn't appear in list
```bash
# Verify task is imported
python -c "import g1_gr00t.tasks; print('OK')"

# Check registration
python scripts/list_envs.py | grep NutPour
```

### GR00T connection fails
1. Verify GR00T server is running: `netstat -an | grep 5555`
2. Check host/port: `--groot_host localhost --groot_port 5555`
3. Test connection: `telnet localhost 5555`

### Assets not found
Assets should be in Isaac Sim Nucleus:
```
$ISAACLAB_NUCLEUS_DIR/Mimic/nut_pour_task/nut_pour_assets/
```

If missing, you may need to download the Isaac Sim asset pack.

## Architecture

This task reuses the modular architecture from `move_cylinder`:

```
g1_gr00t/tasks/nutpour/
├── __init__.py           # Gym registration
├── env_cfg.py           # Scene + robot + MDP config
├── gr00t_client.py      # GR00T client (reused)
└── mdp/
    ├── __init__.py      # MDP module
    ├── observations.py  # Reuses g1_gr00t.observations
    ├── rewards.py       # Placeholder (not used with GR00T)
    ├── terminations.py  # Success conditions
    └── events.py        # Object reset logic
```

## Related Files

- **Documentation**: `docs/NUTPOUR_PORT.md` - Detailed porting notes
- **Summary**: `docs/NUTPOUR_SUMMARY.md` - Quick reference
- **Original**: `IsaacLab/.../nutpour_gr1t2_*.py` - Source files from IsaacLab

## Comparison with Original

| Feature | IsaacLab Original | This Implementation |
|---------|-------------------|---------------------|
| Task ID | `Isaac-NutPour-GR1T2-Pink-IK-Abs-v0` | `G1-NutPour-v0` |
| Robot | GR1T2 (Fourier) | G1 (Unitree) |
| Hands | 22 DOF (11 per hand) | 14 DOF (7 per hand, Dex3) |
| Control | Pink IK + OpenXR tracking | GR00T N1.5 VLA |
| Input | Hand tracking | Vision + state |
| Scene | Same objects, same layout | ✓ |
| Success Criteria | Same thresholds | ✓ |

## Next Steps

1. **Test with GR00T**: Run with actual GR00T server
2. **Tune success thresholds**: Adjust tolerances if needed
3. **Add more tasks**: Follow this template for new scenarios
4. **Improve prompts**: Experiment with task descriptions


