# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Dex3 hand joint state observations (14 DOF)."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def get_robot_hand_joint_states(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Get robot hand joint states (14 DOF: 7 per Dex3 hand).
    
    Returns joint positions, velocities, and torques for Dex3 hands:
    - Left hand: 7 joints (thumb_0, thumb_1, thumb_2, middle_0, middle_1, index_0, index_1)
    - Right hand: 7 joints (same structure)
    
    Args:
        env: The RL environment
    
    Returns:
        torch.Tensor: [batch, 42] tensor containing:
            - [0:14]: joint positions
            - [14:28]: joint velocities
            - [28:42]: joint torques
    """
    # Get all joint states
    joint_pos = env.scene["robot"].data.joint_pos
    joint_vel = env.scene["robot"].data.joint_vel
    joint_torque = env.scene["robot"].data.applied_torque
    
    device = joint_pos.device
    batch = joint_pos.shape[0]
    
    # Define indices for hand joints (14 DOF)
    # Order matches GR00T dataset: left hand (7) then right hand (7)
    hand_joint_indices = [
        31, 37, 41,  # left: thumb_0, thumb_1, thumb_2
        30, 36,      # left: middle_0, middle_1
        29, 35,      # left: index_0, index_1
        34, 40, 42,  # right: thumb_0, thumb_1, thumb_2
        33, 39,      # right: middle_0, middle_1
        32, 38,      # right: index_0, index_1
    ]
    
    # Create index tensor
    idx_t = torch.tensor(hand_joint_indices, dtype=torch.long, device=device)
    idx_batch = idx_t.unsqueeze(0).expand(batch, -1)
    
    # Gather joint states
    pos = torch.gather(joint_pos, 1, idx_batch)
    vel = torch.gather(joint_vel, 1, idx_batch)
    torque = torch.gather(joint_torque, 1, idx_batch)
    
    # Concatenate: [positions, velocities, torques]
    return torch.cat([pos, vel, torque], dim=1)

