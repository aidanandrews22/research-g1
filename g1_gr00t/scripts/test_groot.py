#!/usr/bin/env python3
# python scripts/test_groot.py --task G1-NutPour-v0 --task_description "Pick up the red tube and pour it into the yellow bowl" --video --device cuda:1
# python scripts/test_groot.py --task_description "pick up the cylinder" --video --device cuda:1

"""Script to test G1 environment with GR00T N1.5 policy."""

import argparse

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Test G1 with GR00T policy.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments.")
parser.add_argument("--task", type=str, default="G1-Move-Cylinder-Dex3-v0", help="Task name.")
parser.add_argument("--groot_host", type=str, default="localhost", help="GR00T server host.")
parser.add_argument("--groot_port", type=int, default=5555, help="GR00T server port.")
parser.add_argument("--task_description", type=str, default="pick up the cylinder", help="Task description.")
parser.add_argument("--video", action="store_true", help="Record video.")
parser.add_argument("--video_length", type=int, default=500, help="Video length in steps.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Force settings
args_cli.headless = True
args_cli.enable_cameras = True

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import torch
import os
import json
from datetime import datetime
from pathlib import Path
import numpy as np
import av

from isaaclab_tasks.utils import parse_env_cfg
import g1_gr00t.tasks  # noqa: F401
from g1_gr00t.tasks.move_cylinder.gr00t_client import create_groot_client


def main():
    """Main function."""
    # Parse environment configuration
    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=True
    )
    
    # Create environment
    print(f"[INFO]: Creating environment: {args_cli.task}")
    render_mode = "rgb_array" if args_cli.video else None
    try:
        env = gym.make(args_cli.task, cfg=env_cfg, render_mode=render_mode)
        print(f"[DEBUG]: gym.make() completed")
    except Exception as e:
        print(f"[ERROR]: Failed to create environment: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Print info
    print(f"[DEBUG]: Environment created successfully")
    print(f"[DEBUG]: Getting observation space...")
    try:
        obs_space = env.observation_space
        print(f"[INFO]: Observation space: {obs_space}")
    except Exception as e:
        print(f"[ERROR]: Failed to get observation space: {e}")
        import traceback
        traceback.print_exc()
        env.close()
        return
    
    print(f"[DEBUG]: Getting action space...")
    try:
        act_space = env.action_space
        print(f"[INFO]: Action space: {act_space}")
    except Exception as e:
        print(f"[ERROR]: Failed to get action space: {e}")
        import traceback
        traceback.print_exc()
        env.close()
        return
    
    # Create output directory first
    output_dir = Path(f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}/{args_cli.task}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO]: Logging to {output_dir}")
    
    # Create and connect GR00T client
    print(f"\n[INFO]: Creating GR00T client...")
    groot_client = create_groot_client(
        host=args_cli.groot_host,
        port=args_cli.groot_port,
        task_description=args_cli.task_description,
        log_dir=output_dir
    )
    
    print(f"[INFO]: Connecting to GR00T server at {args_cli.groot_host}:{args_cli.groot_port}...")
    groot_client.connect()
    
    if not groot_client.is_connected():
        print("[ERROR]: Failed to connect to GR00T server. Exiting.")
        env.close()
        return
    
    # Reset environment
    print("\n[INFO]: Resetting environment...")
    obs, _ = env.reset()
    
    # Set up robot state logging
    robot_log_file = output_dir / "robot_states.jsonl"
    
    # Set up video recording if requested
    video_containers = {}
    video_streams = {}
    video_dir = None
    if args_cli.video:
        video_dir = output_dir
        print(f"[INFO]: Recording videos to {video_dir}")
        
        # Set up video writers for each camera using PyAV
        if hasattr(env.unwrapped.scene, 'sensors'):
            for sensor_name, sensor in env.unwrapped.scene.sensors.items():
                if 'camera' in sensor_name.lower():
                    try:
                        first_frame = sensor.data.output['rgb'][0].cpu().numpy()
                        height, width = first_frame.shape[:2]
                        video_path = video_dir / f"{sensor_name}.mp4"
                        
                        # Create PyAV container with H.264 codec
                        container = av.open(str(video_path), mode='w')
                        stream = container.add_stream('h264', rate=50)  # 50 fps
                        stream.width = width
                        stream.height = height
                        stream.pix_fmt = 'yuv420p'
                        stream.options = {'crf': '23', 'preset': 'medium'}
                        
                        video_containers[sensor_name] = container
                        video_streams[sensor_name] = stream
                        print(f"[INFO]: Recording {sensor_name} ({width}x{height}) at 50 fps")
                    except Exception as e:
                        print(f"[WARNING]: Could not setup recording for {sensor_name}: {e}")
    
    print(f"\n[INFO]: Running simulation with GR00T policy...")
    print(f"[INFO]: Task: {args_cli.task_description}")
    
    step_count = 0
    max_steps = args_cli.video_length if args_cli.video else 1000
    frames_written = {name: 0 for name in video_containers.keys()}
    
    try:
        while simulation_app.is_running() and step_count < max_steps:
            with torch.inference_mode():
                # Get action from GR00T
                actions = groot_client.get_action(obs['policy'], env)
                
                # Log action before sending to robot
                action_before_log = {
                    "step": step_count + 1,
                    "timestamp": datetime.now().isoformat(),
                    "type": "action_to_robot",
                    "action": actions.cpu().numpy().tolist()
                }
                with open(robot_log_file, 'a') as f:
                    f.write(json.dumps(action_before_log) + '\n')
                
                # Expand to batch dimension
                actions = actions.unsqueeze(0).to(env.unwrapped.device)
                
                # Step environment
                obs, reward, terminated, truncated, info = env.step(actions)
                step_count += 1
                
                # Log actual robot state after action injection
                body_state = obs['policy']['robot_body_state'][0].cpu().numpy()
                hand_state = obs['policy']['robot_hand_state'][0].cpu().numpy()
                
                # Extract joint positions (every 3rd value)
                body_positions = body_state[::3]
                hand_positions = hand_state[::3]
                full_state = np.concatenate([body_positions, hand_positions])
                
                # Extract arm and hand positions (indices matching client)
                left_arm_indices = list(range(15, 22))
                right_arm_indices = list(range(29, 36))
                left_hand_indices = list(range(22, 29))
                right_hand_indices = list(range(36, 43))
                
                actual_state_log = {
                    "step": step_count,
                    "timestamp": datetime.now().isoformat(),
                    "type": "robot_actual_state",
                    "joint_positions": {
                        "left_arm": full_state[left_arm_indices].tolist(),
                        "right_arm": full_state[right_arm_indices].tolist(),
                        "left_hand": full_state[left_hand_indices].tolist(),
                        "right_hand": full_state[right_hand_indices].tolist()
                    },
                    "full_state": full_state.tolist(),
                    "reward": float(reward[0].item())
                }
                with open(robot_log_file, 'a') as f:
                    f.write(json.dumps(actual_state_log) + '\n')
                
                # Record video frames using PyAV
                if args_cli.video and video_containers:
                    for sensor_name, sensor in env.unwrapped.scene.sensors.items():
                        if sensor_name in video_containers:
                            try:
                                img_data = sensor.data.output['rgb'][0].cpu().numpy()
                                if img_data.dtype != np.uint8:
                                    img_data = (np.clip(img_data, 0, 1) * 255).astype(np.uint8)
                                
                                # Create PyAV VideoFrame from numpy array
                                frame = av.VideoFrame.from_ndarray(img_data, format='rgb24')
                                
                                # Encode and write frame
                                for packet in video_streams[sensor_name].encode(frame):
                                    video_containers[sensor_name].mux(packet)
                                
                                frames_written[sensor_name] += 1
                            except Exception as e:
                                if step_count == 1:  # Only print on first error
                                    print(f"[WARNING]: Error writing frame for {sensor_name}: {e}")
                
                # Print progress
                if step_count % 50 == 0:
                    print(f"[INFO]: Step {step_count}/{max_steps}, Reward: {reward[0].item():.4f}")
                
                # Reset if done
                if terminated[0] or truncated[0]:
                    print(f"[INFO]: Episode finished at step {step_count}")
                    obs, _ = env.reset()
    
    except KeyboardInterrupt:
        print("\n[INFO]: Interrupted by user")
    
    finally:
        # Close video containers and flush remaining packets
        if args_cli.video and video_containers:
            for sensor_name, container in video_containers.items():
                try:
                    # Flush remaining packets
                    stream = video_streams[sensor_name]
                    for packet in stream.encode():
                        container.mux(packet)
                    
                    # Close container
                    container.close()
                    frame_count = frames_written.get(sensor_name, 0)
                    print(f"[INFO]: Saved {sensor_name}.mp4 ({frame_count} frames)")
                except Exception as e:
                    print(f"[WARNING]: Error closing video for {sensor_name}: {e}")
            print(f"[INFO]: Videos saved to {video_dir}")
        
        # Disconnect GR00T
        groot_client.disconnect()
        
        # Close environment
        env.close()
    
    print("\n[INFO]: Test complete!")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()

