#!/usr/bin/env python3
# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

"""Basic test script to verify environment can be created without GR00T."""

import argparse

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Test environment creation.")
parser.add_argument("--task", type=str, default="G1-NutPour-v0", help="Task name.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import torch

from isaaclab_tasks.utils import parse_env_cfg
import g1_gr00t.tasks  # noqa: F401


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
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)
    
    # Print info
    print(f"[INFO]: Observation space: {env.observation_space}")
    print(f"[INFO]: Action space: {env.action_space}")
    
    # Reset environment
    print("\n[INFO]: Resetting environment...")
    obs, _ = env.reset()
    
    print(f"[INFO]: Observation keys: {obs.keys()}")
    for key, value in obs.items():
        if isinstance(value, torch.Tensor):
            print(f"  {key}: shape={value.shape}, dtype={value.dtype}")
        else:
            print(f"  {key}: {type(value)}")
    
    # Try a few random steps
    print("\n[INFO]: Running 10 random steps...")
    for i in range(10):
        # Random actions
        actions = torch.randn(env.num_envs, env.action_space.shape[0], device=env.unwrapped.device) * 0.1
        obs, reward, terminated, truncated, info = env.step(actions)
        
        if i % 5 == 0:
            print(f"  Step {i}: reward={reward[0].item():.4f}")
    
    # Close environment
    env.close()
    print("\n[INFO]: Test complete! Environment works correctly.")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()


