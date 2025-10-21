#!/usr/bin/env python3
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

"""Script to test environment and save camera images to disk."""

import argparse
import os
from pathlib import Path

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Test G1 environment and save images.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments.")
parser.add_argument("--task", type=str, default="G1-Move-Cylinder-Dex3-v0", help="Task name.")
parser.add_argument("--output_dir", type=str, default="/tmp/g1_images", help="Output directory for images.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Force headless mode
args_cli.headless = True
args_cli.enable_cameras = True

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import torch
import numpy as np
from PIL import Image

from isaaclab_tasks.utils import parse_env_cfg
import g1_gr00t.tasks  # noqa: F401


def save_image(data: torch.Tensor, path: str):
    """Save image tensor to file."""
    # Convert from torch tensor to numpy
    img_np = data.cpu().numpy()
    
    # Handle different image formats
    if img_np.ndim == 4:  # (batch, height, width, channels)
        img_np = img_np[0]  # Take first image
    
    # Convert to uint8 if needed
    if img_np.dtype == np.float32 or img_np.dtype == np.float64:
        img_np = (img_np * 255).astype(np.uint8)
    
    # Create PIL image and save
    img = Image.fromarray(img_np)
    img.save(path)
    print(f"[INFO]: Saved image to {path}")


def main():
    """Main function."""
    # Create output directory
    output_dir = Path(args_cli.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO]: Output directory: {output_dir}")
    
    # Parse environment configuration
    env_cfg = parse_env_cfg(
        args_cli.task, 
        device=args_cli.device, 
        num_envs=args_cli.num_envs, 
        use_fabric=True
    )
    
    # Create environment
    print(f"[INFO]: Creating environment: {args_cli.task}")
    env = gym.make(args_cli.task, cfg=env_cfg)
    
    # Print info
    print(f"[INFO]: Observation space: {env.observation_space}")
    print(f"[INFO]: Action space: {env.action_space}")
    
    # Reset environment
    print("[INFO]: Resetting environment...")
    obs, _ = env.reset()
    
    print("\n[INFO]: Environment loaded successfully!")
    print("[INFO]: Robot with 43 DOF (29 body + 14 hand joints)")
    print(f"[INFO]: Robot body state shape: {obs['policy']['robot_body_state'].shape}")
    print(f"[INFO]: Robot hand state shape: {obs['policy']['robot_hand_state'].shape}")
    
    # Run for a few steps and capture observations
    print(f"\n[INFO]: Running simulation for 100 steps...")
    
    for step in range(100):
        # Zero actions
        actions = torch.zeros(env.action_space.shape, device=env.unwrapped.device)
        
        # Step environment
        obs, reward, terminated, truncated, info = env.step(actions)
        
        # Save some diagnostic info every 25 steps
        if step % 25 == 0:
            print(f"\n[Step {step}]")
            print(f"  Robot body state (first 10): {obs['policy']['robot_body_state'][0, :10].tolist()}")
            print(f"  Robot hand state (first 10): {obs['policy']['robot_hand_state'][0, :10].tolist()}")
            print(f"  Reward: {reward[0].item():.4f}")
            
            # Try to get actual camera images from the scene if cameras exist
            if hasattr(env.unwrapped.scene, 'sensors'):
                for sensor_name, sensor in env.unwrapped.scene.sensors.items():
                    if 'camera' in sensor_name.lower():
                        try:
                            if hasattr(sensor, 'data') and hasattr(sensor.data, 'output'):
                                if 'rgb' in sensor.data.output:
                                    img_data = sensor.data.output['rgb']
                                    img_path = output_dir / f"{sensor_name}_step_{step:04d}.png"
                                    save_image(img_data, str(img_path))
                        except Exception as e:
                            print(f"  [WARNING]: Could not save {sensor_name}: {e}")
    
    print(f"\n[INFO]: Simulation complete. Check {output_dir} for saved images.")
    print("[INFO]: Scene contains:")
    print(f"  - G1 Robot at position (-3.9, -2.8, 0.8)")
    print(f"  - Warehouse environment")
    print(f"  - Packing tables")
    print(f"  - Cylinder object")
    
    # Close environment
    env.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()

