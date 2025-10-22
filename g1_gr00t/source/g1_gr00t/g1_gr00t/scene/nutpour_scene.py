# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Scene configuration for NutPour task with table and manipulation objects."""

import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg, GroundPlaneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAACLAB_NUCLEUS_DIR


@configclass
class NutPourSceneCfg(InteractiveSceneCfg):
    """Scene configuration for NutPour manipulation task.
    
    Task involves:
    1. Picking up sorting bowl and placing it on sorting scale
    2. Picking up factory nut and placing it in the sorting bowl
    3. Picking up sorting beaker and placing it in the black sorting bin
    
    This is the base scene that will be extended with robot and cameras in the task configuration.
    """

    # Table - workspace surface
    table = AssetBaseCfg(
        prim_path="/World/envs/env_.*/Table",
        init_state=AssetBaseCfg.InitialStateCfg(pos=[0.0, 0.55, 0.0], rot=[1.0, 0.0, 0.0, 0.0]),
        spawn=UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Mimic/nut_pour_task/nut_pour_assets/table.usd",
            scale=(1.0, 1.0, 1.3),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
        ),
    )

    # Sorting scale - target location for bowl
    sorting_scale = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/SortingScale",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[0.22236, 0.56, 0.9859], rot=[1, 0, 0, 0]),
        spawn=UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Mimic/nut_pour_task/nut_pour_assets/sorting_scale.usd",
            scale=(1.0, 1.0, 1.0),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
        ),
    )

    # Sorting bowl (yellow) - to be filled with nut and placed on scale
    sorting_bowl = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/SortingBowl",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[0.02779, 0.43007, 0.9860], rot=[1, 0, 0, 0]),
        spawn=UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Mimic/nut_pour_task/nut_pour_assets/sorting_bowl_yellow.usd",
            scale=(1.0, 1.0, 1.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=0.005),
        ),
    )

    # Sorting beaker (red) - to be discarded into bin
    sorting_beaker = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/SortingBeaker",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[-0.13739, 0.45793, 0.9861], rot=[1, 0, 0, 0]),
        spawn=UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Mimic/nut_pour_task/nut_pour_assets/sorting_beaker_red.usd",
            scale=(0.45, 0.45, 1.3),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
        ),
    )

    # Factory nut (green) - to be placed in bowl
    factory_nut = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/FactoryNut",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[-0.13739, 0.45793, 0.9995], rot=[1, 0, 0, 0]),
        spawn=UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Mimic/nut_pour_task/nut_pour_assets/factory_m16_nut_green.usd",
            scale=(0.5, 0.5, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=0.005),
        ),
    )

    # Black sorting bin (blue) - target location for beaker
    black_sorting_bin = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/BlackSortingBin",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[-0.32688, 0.46793, 0.98634], rot=[1.0, 0, 0, 0]),
        spawn=UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Mimic/nut_pour_task/nut_pour_assets/sorting_bin_blue.usd",
            scale=(0.75, 1.0, 1.0),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
        ),
    )

    # Ground plane
    ground = AssetBaseCfg(
        prim_path="/World/GroundPlane",
        spawn=GroundPlaneCfg(),
    )

    # Lighting
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(
            color=(0.75, 0.75, 0.75),
            intensity=3000.0
        ),
    )


