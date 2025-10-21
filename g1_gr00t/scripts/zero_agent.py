# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Script to run an environment with zero action agent."""

"""Launch Isaac Sim Simulator first."""

import os
from datetime import datetime
import argparse
from pathlib import Path
import cv2
import numpy as np

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Zero agent for Isaac Lab environments.")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument("--video", action="store_true", default=False, help="Record video of the simulation.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video in steps.")
parser.add_argument("--video_interval", type=int, default=2, help="Interval between captured frames.")
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli = parser.parse_args()
args_cli.enable_cameras = True
args_cli.headless = True
args_cli.hide_ui = False

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import torch

from isaaclab_tasks.utils import parse_env_cfg

import g1_gr00t.tasks  # noqa: F401


def main():
    """Zero actions agent with Isaac Lab environment."""
    # Set default task if not provided
    if args_cli.task is None:
        args_cli.task = "G1-Move-Cylinder-Dex3-v0"
    
    # Set default num_envs if not provided
    if args_cli.num_envs is None:
        args_cli.num_envs = 1
    
    # parse configuration
    env_cfg = parse_env_cfg(
        args_cli.task, device=args_cli.device, num_envs=args_cli.num_envs, use_fabric=not args_cli.disable_fabric
    )
    # create environment
    render_mode = "rgb_array" if args_cli.video else None
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode=render_mode)

    # print info (this is vectorized environment)
    print(f"[INFO]: Gym observation space: {env.observation_space}")
    print(f"[INFO]: Gym action space: {env.action_space}")
    
    # reset environment first
    env.reset()
    
    # Set up video recording from scene cameras if requested
    video_writers = {}
    video_dir = None
    if args_cli.video:
        video_dir = Path(f"videos/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}/{args_cli.task}")
        video_dir.mkdir(parents=True, exist_ok=True)
        print(f"[INFO]: Recording videos to {video_dir}")
        print(f"[INFO]: Video length: {args_cli.video_length} steps")
        
        # Find all cameras in the scene and create video writers
        if hasattr(env.unwrapped.scene, 'sensors'):
            for sensor_name, sensor in env.unwrapped.scene.sensors.items():
                if 'camera' in sensor_name.lower():
                    try:
                        if hasattr(sensor, 'data') and hasattr(sensor.data, 'output'):
                            if 'rgb' in sensor.data.output:
                                # Get first frame to determine dimensions
                                first_frame = sensor.data.output['rgb'][0].cpu().numpy()
                                height, width = first_frame.shape[:2]
                                
                                # Create video writer
                                video_path = video_dir / f"{sensor_name}.mp4"
                                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                                fps = 20
                                writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
                                
                                if writer.isOpened():
                                    video_writers[sensor_name] = writer
                                    print(f"[INFO]: Recording {sensor_name} ({width}x{height})")
                                else:
                                    print(f"[WARNING]: Could not open video writer for {sensor_name}")
                    except Exception as e:
                        print(f"[WARNING]: Could not setup recording for {sensor_name}: {e}")
    
    # simulate environment
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension("omni.services.livestream.nvcf")
    simulation_app.set_setting("/app/window/drawMouse", True)
    
    # Option to save USD file for local viewing
    if False:  # Set to True to save USD file
        output_path = "/tmp/g1_scene.usd"
        stage = get_current_stage()
        stage.Export(output_path)
        print(f"[INFO]: Scene saved to {output_path}")
        print("[INFO]: You can view this file locally with Isaac Sim or USD viewer")
    
    if not args_cli.video:
        print("[INFO]: Simulation running. Connect via WebRTC to view the scene.")
        print("[INFO]: If you see a blank screen, use mouse controls to navigate the viewport.")
        print("[INFO]: WebRTC URL should be shown in the terminal or check the Isaac Sim logs")
    
    step_count = 0
    max_steps = args_cli.video_length if args_cli.video else float('inf')
    
    while simulation_app.is_running() and step_count < max_steps:
        # run everything in inference mode
        with torch.inference_mode():
            # compute zero actions
            actions = torch.zeros(env.action_space.shape, device=env.unwrapped.device)
            # apply actions
            env.step(actions)
            step_count += 1
            
            # Capture frames from all cameras if recording
            if args_cli.video and video_writers:
                if hasattr(env.unwrapped.scene, 'sensors'):
                    for sensor_name, sensor in env.unwrapped.scene.sensors.items():
                        if sensor_name in video_writers:
                            try:
                                img_data = sensor.data.output['rgb'][0].cpu().numpy()
                                
                                # Convert to uint8 if needed
                                if img_data.dtype != np.uint8:
                                    img_data = (np.clip(img_data, 0, 1) * 255).astype(np.uint8)
                                
                                # Convert RGB to BGR for OpenCV
                                frame_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
                                
                                # Write frame
                                video_writers[sensor_name].write(frame_bgr)
                            except Exception as e:
                                if step_count == 1:  # Only print error once
                                    print(f"[WARNING]: Error capturing frame for {sensor_name}: {e}")
            
            if args_cli.video and step_count % 50 == 0:
                print(f"[INFO]: Recording... {step_count}/{args_cli.video_length} steps")
    
    # Release video writers
    if args_cli.video and video_writers:
        for sensor_name, writer in video_writers.items():
            writer.release()
            print(f"[INFO]: Saved {sensor_name}.mp4")
        print(f"[INFO]: Video recording complete! Check {video_dir}")

    # close the simulator
    env.close()


if __name__ == "__main__":
    # run the main function
    main()
    # close sim app
    simulation_app.close()
