# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Scene configuration with warehouse, tables, and cylinder object."""

import os
import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg
from isaaclab.utils import configclass

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@configclass
class CylinderSceneCfg(InteractiveSceneCfg):
    """Scene configuration with warehouse environment, tables, and cylinder.
    
    This is the base scene that will be extended with robot and cameras in the task configuration.
    """

    # Warehouse room environment
    room_walls = AssetBaseCfg(
        prim_path="/World/envs/env_.*/Room",
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=[0.0, 0.0, 0],
            rot=[1.0, 0.0, 0.0, 0.0]
        ),
        spawn=UsdFileCfg(
            usd_path=f"{PROJECT_ROOT}/assets/objects/small_warehouse/small_warehouse_digital_twin.usd",
        ),
    )

    # First packing table
    packing_table1 = AssetBaseCfg(
        prim_path="/World/envs/env_.*/PackingTable_1",
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=[-2.35644, -3.45572, -0.2],
            rot=[0.70091, 0.0, 0.0, 0.71325]
        ),
        spawn=UsdFileCfg(
            usd_path=f"{PROJECT_ROOT}/assets/objects/PackingTable_2/PackingTable.usd",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
        ),
    )

    # Second packing table
    packing_table2 = AssetBaseCfg(
        prim_path="/World/envs/env_.*/PackingTable_2",
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=[-3.97225, -4.3424, -0.2],
            rot=[1.0, 0.0, 0.0, 0.0]
        ),
        spawn=UsdFileCfg(
            usd_path=f"{PROJECT_ROOT}/assets/objects/PackingTable/PackingTable.usd",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
        ),
    )

    # Cylinder object for manipulation
    object = RigidObjectCfg(
        prim_path="/World/envs/env_.*/Object",
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=[-2.63514, -2.78975, 0.84],  # Moved back 0.05m (further from robot)
            rot=[1, 0, 0, 0],
            lin_vel=[0.0, 0.0, 0.0],  # Zero linear velocity
            ang_vel=[0.0, 0.0, 0.0],  # Zero angular velocity
        ),
        spawn=sim_utils.CylinderCfg(
            radius=0.018,
            height=0.35,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.4),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.15, 0.15, 0.15),
                metallic=1.0
            ),
            physics_material=sim_utils.RigidBodyMaterialCfg(
                friction_combine_mode="max",
                restitution_combine_mode="min",
                static_friction=1.5,
                dynamic_friction=1.5,
                restitution=0.0,
            ),
        ),
    )

    # Ground plane for reference
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0, 0, -0.5)),
        spawn=sim_utils.GroundPlaneCfg(
            color=(0.2, 0.2, 0.2),
            size=(100.0, 100.0),
        ),
    )
    
    # Lighting
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(
            color=(0.75, 0.75, 0.75),
            intensity=3000.0
        ),
    )

