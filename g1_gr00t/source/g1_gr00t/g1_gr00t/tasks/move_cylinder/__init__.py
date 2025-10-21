# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""G1 cylinder manipulation task for GR00T integration."""

import gymnasium as gym

from . import env_cfg

gym.register(
    id="G1-Move-Cylinder-Dex3-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": env_cfg.MoveCylinderEnvCfg,
    },
    disable_env_checker=True,
)

