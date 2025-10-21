# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""G1 body joint state observations (29 DOF)."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def get_robot_body_joint_states(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Get robot body joint states (29 DOF: legs + waist + arms).
    
    Returns joint positions, velocities, and torques for:
    - 12 leg joints (6 per leg)
    - 3 waist joints
    - 14 arm joints (7 per arm)
    
    Args:
        env: The RL environment
    
    Returns:
        torch.Tensor: [batch, 87] tensor containing:
            - [0:29]: joint positions
            - [29:58]: joint velocities
            - [58:87]: joint torques
    """
    # Get all joint states
    joint_pos = env.scene["robot"].data.joint_pos
    joint_vel = env.scene["robot"].data.joint_vel
    joint_torque = env.scene["robot"].data.applied_torque
    
    device = joint_pos.device
    batch = joint_pos.shape[0]
    
    # Define indices for body joints (29 DOF, excluding hands)
    # Order: left_leg(6), right_leg(6), waist(3), left_arm(7), right_arm(7)
    body_joint_indices = [
        0, 3, 6, 9, 13, 17,  # left leg: hip_pitch, hip_roll, hip_yaw, knee, ankle_pitch, ankle_roll
        1, 4, 7, 10, 14, 18,  # right leg: same order
        2, 5, 8,  # waist: yaw, roll, pitch
        11, 15, 19, 21, 23, 25, 27,  # left arm: shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll, wrist_pitch, wrist_yaw
        12, 16, 20, 22, 24, 26, 28,  # right arm: same order
    ]
    
    # Create index tensor
    idx_t = torch.tensor(body_joint_indices, dtype=torch.long, device=device)
    idx_batch = idx_t.unsqueeze(0).expand(batch, -1)
    
    # Gather joint states
    pos = torch.gather(joint_pos, 1, idx_batch)
    vel = torch.gather(joint_vel, 1, idx_batch)
    torque = torch.gather(joint_torque, 1, idx_batch)
    
    # Concatenate: [positions, velocities, torques]
    return torch.cat([pos, vel, torque], dim=1)

