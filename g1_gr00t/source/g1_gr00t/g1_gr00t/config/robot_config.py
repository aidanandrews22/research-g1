# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""G1 Robot Configuration for 43 DOF Dex3 Wholebody Control."""

import os
import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg
from isaaclab.utils import configclass

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@configclass
class G1Dex3WholebodyConfig:
    """G1 Robot with 43 DOF Dex3 hands - wholebody control configuration.
    
    DOF breakdown:
    - 12 leg joints (6 per leg)
    - 3 waist joints
    - 14 arm joints (7 per arm)
    - 14 hand joints (7 per hand, Dex3 configuration)
    Total: 43 DOF
    
    Joint names match GR00T dataset exactly.
    """


G1_DEX3_43DOF_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=f"{PROJECT_ROOT}/assets/robots/g1-29dof_wholebody_dex3/g1_29dof_with_dex3_rev_1_0.usd",
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=1,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.80),
        joint_pos={
            # Leg joints - standing pose
            ".*_hip_pitch_joint": -0.20,
            ".*_knee_joint": 0.42,
            ".*_ankle_pitch_joint": -0.23,
            
            # Arm joints - reaching pose
            ".*_elbow_joint": 0.87,
            "left_shoulder_roll_joint": 0.18,
            "left_shoulder_pitch_joint": 0.35,
            "right_shoulder_roll_joint": -0.18,
            "right_shoulder_pitch_joint": 0.35,
            
            # Hand joints (Dex3) - neutral/open pose
            "left_hand_index_0_joint": 0.0,
            "left_hand_middle_0_joint": 0.0,
            "left_hand_thumb_0_joint": 0.0,
            "left_hand_index_1_joint": 0.0,
            "left_hand_middle_1_joint": 0.0,
            "left_hand_thumb_1_joint": 0.0,
            "left_hand_thumb_2_joint": 0.0,
            
            "right_hand_index_0_joint": 0.0,
            "right_hand_middle_0_joint": 0.0,
            "right_hand_thumb_0_joint": 0.0,
            "right_hand_index_1_joint": 0.0,
            "right_hand_middle_1_joint": 0.0,
            "right_hand_thumb_1_joint": 0.0,
            "right_hand_thumb_2_joint": 0.0,
        },
        joint_vel={".*": 0.0},
    ),
    soft_joint_pos_limit_factor=0.90,
    actuators={
        # Legs and waist - LOCKED with very high stiffness to prevent movement
        "legs": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_hip_yaw_joint",
                ".*_hip_roll_joint",
                ".*_hip_pitch_joint",
                ".*_knee_joint",
                ".*waist.*",
            ],
            effort_limit_sim={
                ".*_hip_yaw_joint": 88.0,
                ".*_hip_roll_joint": 139.0,
                ".*_hip_pitch_joint": 88.0,
                ".*_knee_joint": 139.0,
                ".*waist_yaw_joint": 88.0,
                ".*waist_roll_joint": 35.0,
                ".*waist_pitch_joint": 35.0,
            },
            velocity_limit_sim={
                ".*_hip_yaw_joint": 0.01,  # Nearly zero velocity
                ".*_hip_roll_joint": 0.01,
                ".*_hip_pitch_joint": 0.01,
                ".*_knee_joint": 0.01,
                ".*waist_yaw_joint": 0.01,
                ".*waist_roll_joint": 0.01,
                ".*waist_pitch_joint": 0.01,
            },
            stiffness={
                ".*_hip_yaw_joint": 10000.0,  # Very high stiffness to lock
                ".*_hip_roll_joint": 10000.0,
                ".*_hip_pitch_joint": 10000.0,
                ".*_knee_joint": 10000.0,
                ".*waist.*": 10000.0,
            },
            damping={
                ".*_hip_yaw_joint": 1000.0,  # High damping to prevent oscillation
                ".*_hip_roll_joint": 1000.0,
                ".*_hip_pitch_joint": 1000.0,
                ".*_knee_joint": 1000.0,
                ".*waist.*": 1000.0,
            },
            armature=0.01,
        ),
        # Feet - LOCKED
        "feet": ImplicitActuatorCfg(
            joint_names_expr=[".*_ankle_pitch_joint", ".*_ankle_roll_joint"],
            effort_limit_sim={
                ".*_ankle_pitch_joint": 35.0,
                ".*_ankle_roll_joint": 35.0,
            },
            velocity_limit_sim={
                ".*_ankle_pitch_joint": 0.01,
                ".*_ankle_roll_joint": 0.01,
            },
            stiffness=10000.0,  # Very high stiffness to lock
            damping=1000.0,  # High damping
            armature=0.01,
        ),
        # Shoulders
        "shoulders": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_shoulder_pitch_joint",
                ".*_shoulder_roll_joint",
            ],
            effort_limit_sim={
                ".*_shoulder_pitch_joint": 25.0,
                ".*_shoulder_roll_joint": 25.0,
            },
            velocity_limit_sim={
                ".*_shoulder_pitch_joint": 37.0,
                ".*_shoulder_roll_joint": 37.0,
            },
            stiffness=100.0,
            damping=2.0,
            armature=0.01,
        ),
        # Arms (shoulder yaw and elbow)
        "arms": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_shoulder_yaw_joint",
                ".*_elbow_joint",
            ],
            effort_limit_sim={
                ".*_shoulder_yaw_joint": 25.0,
                ".*_elbow_joint": 25.0,
            },
            velocity_limit_sim={
                ".*_shoulder_yaw_joint": 37.0,
                ".*_elbow_joint": 37.0,
            },
            stiffness=50.0,
            damping=2.0,
            armature=0.01,
        ),
        # Wrists
        "wrist": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_wrist_.*",
            ],
            effort_limit_sim={
                ".*_wrist_yaw_joint": 5.0,
                ".*_wrist_roll_joint": 25.0,
                ".*_wrist_pitch_joint": 5.0,
            },
            velocity_limit_sim={
                ".*_wrist_yaw_joint": 22.0,
                ".*_wrist_roll_joint": 37.0,
                ".*_wrist_pitch_joint": 22.0,
            },
            stiffness=40.0,
            damping=2.0,
            armature=0.01,
        ),
        # Hands (Dex3 - 7 DOF per hand)
        "hands": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_hand_index_.*_joint",
                ".*_hand_middle_.*_joint",
                ".*_hand_thumb_.*_joint",
            ],
            effort_limit=300,
            velocity_limit=100.0,
            stiffness={
                ".*": 100.0,
            },
            damping={
                ".*": 10.0,
            },
            armature={
                ".*": 0.1,
            },
        ),
    },
)

