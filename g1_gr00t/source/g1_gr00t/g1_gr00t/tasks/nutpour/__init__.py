# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""G1 NutPour manipulation task for GR00T integration."""

import gymnasium as gym

from . import env_cfg

gym.register(
    id="G1-NutPour-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": env_cfg.NutPourEnvCfg,
    },
    disable_env_checker=True,
)


