# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Reward functions for nutpour task."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def compute_reward(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Placeholder reward function.
    
    Returns constant reward for now. Can be updated later with actual task rewards.
    
    Args:
        env: The RL environment
    
    Returns:
        torch.Tensor: Reward value for each environment [batch]
    """
    # Return zero rewards (placeholder)
    return torch.zeros(env.num_envs, device=env.device)


__all__ = ["compute_reward"]


