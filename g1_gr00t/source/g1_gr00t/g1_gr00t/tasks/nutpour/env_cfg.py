# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Environment configuration for G1 NutPour manipulation task."""

import torch
import isaaclab.sim as sim_utils
import isaaclab.envs.mdp as base_mdp
from isaaclab.assets import ArticulationCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import EventTermCfg
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass

from g1_gr00t.config import G1_DEX3_43DOF_CFG, CameraPresets
from g1_gr00t.scene import NutPourSceneCfg as BaseNutPourSceneCfg
from . import mdp


@configclass
class NutPourTaskSceneCfg(BaseNutPourSceneCfg):
    """Scene configuration with G1 robot and cameras added."""
    
    # G1 robot with 43 DOF (Dex3 hands)
    # Position robot in front of table
    robot: ArticulationCfg = G1_DEX3_43DOF_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.93),
            rot=(0.7071, 0, 0, 0.7071),  # 90 degree rotation to face table
            joint_pos={
                # Leg joints - standing pose (locked)
                ".*_hip_pitch_joint": -0.20,
                ".*_knee_joint": 0.42,
                ".*_ankle_pitch_joint": -0.23,
                
                # Arm joints - neutral reaching pose
                ".*_elbow_joint": -1.0,  # Within joint limits [-1.047, 2.094]
                "left_shoulder_roll_joint": 0.0,
                "left_shoulder_pitch_joint": 0.0,
                "right_shoulder_roll_joint": 0.0,
                "right_shoulder_pitch_joint": 0.0,
                
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
        # Lock the base and legs by making them kinematic
        spawn=G1_DEX3_43DOF_CFG.spawn.replace(
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
                fix_root_link=True,  # Lock the base in place
            ),
        ),
    )
    
    # Contact sensors
    contact_forces = ContactSensorCfg(
        prim_path="/World/envs/env_.*/Robot/.*",
        history_length=10,
        track_air_time=True,
        debug_vis=False,
    )
    
    # Cameras
    front_camera = CameraPresets.g1_front_camera()
    left_wrist_camera = CameraPresets.left_dex3_wrist_camera()
    right_wrist_camera = CameraPresets.right_dex3_wrist_camera()
    robot_camera = CameraPresets.g1_world_camera()


@configclass
class ActionsCfg:
    """Action configuration for direct joint position control.
    
    Only control arms and hands (28 DOF total):
    - 14 arm joints (7 per arm: shoulder pitch/roll/yaw, elbow, wrist yaw/roll/pitch)
    - 14 hand joints (7 per hand: Dex3 configuration)
    
    Legs and waist are locked in place.
    """
    
    joint_pos = base_mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            # Arms (14 DOF)
            ".*_shoulder_pitch_joint",
            ".*_shoulder_roll_joint",
            ".*_shoulder_yaw_joint",
            ".*_elbow_joint",
            ".*_wrist_yaw_joint",
            ".*_wrist_roll_joint",
            ".*_wrist_pitch_joint",
            # Hands (14 DOF - Dex3)
            ".*_hand_index_0_joint",
            ".*_hand_middle_0_joint",
            ".*_hand_thumb_0_joint",
            ".*_hand_index_1_joint",
            ".*_hand_middle_1_joint",
            ".*_hand_thumb_1_joint",
            ".*_hand_thumb_2_joint",
        ],
        scale=1.0,
        use_default_offset=False,  # GR00T outputs absolute positions, not offsets!
    )


@configclass
class ObservationsCfg:
    """Observation configuration."""
    
    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for policy."""
        
        # Body joints (29 DOF: legs + waist + arms)
        robot_body_state = ObsTerm(func=mdp.get_robot_body_joint_states)
        
        # Hand joints (14 DOF: Dex3 hands)
        robot_hand_state = ObsTerm(func=mdp.get_robot_hand_joint_states)
        
        # Camera images
        camera_images = ObsTerm(func=mdp.get_camera_images)
        
        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False  # Keep observations separate
    
    policy: PolicyCfg = PolicyCfg()


@configclass
class RewardsCfg:
    """Reward configuration."""
    
    # Placeholder reward
    reward = RewTerm(func=mdp.compute_reward, weight=1.0)


@configclass
class TerminationsCfg:
    """Termination configuration."""
    
    # Time out
    time_out = DoneTerm(func=base_mdp.time_out, time_out=True)


@configclass
class EventCfg:
    """Event configuration."""
    
    # Reset object positions with slight randomization
    reset_object = EventTermCfg(
        func=mdp.reset_object_poses_nut_pour,
        mode="reset",
        params={
            "pose_range": {
                "x": (-0.02, 0.02),
                "y": (-0.02, 0.02),
                "z": (0.0, 0.0),
                "roll": (0.0, 0.0),
                "pitch": (0.0, 0.0),
                "yaw": (-0.1, 0.1),
            },
            "sorting_beaker_cfg": SceneEntityCfg("sorting_beaker"),
            "factory_nut_cfg": SceneEntityCfg("factory_nut"),
            "sorting_bowl_cfg": SceneEntityCfg("sorting_bowl"),
            "sorting_scale_cfg": SceneEntityCfg("sorting_scale"),
        },
    )


@configclass
class NutPourEnvCfg(ManagerBasedRLEnvCfg):
    """Configuration for G1 NutPour manipulation environment."""
    
    # Scene settings
    scene: NutPourTaskSceneCfg = NutPourTaskSceneCfg(
        num_envs=1,
        env_spacing=2.5,
        replicate_physics=True,
    )
    
    # MDP settings
    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventCfg = EventCfg()
    
    # No commands or curriculum for now
    commands = None
    curriculum = None
    
    def __post_init__(self):
        """Post initialization."""
        # General settings
        self.decimation = 4
        self.episode_length_s = 20.0
        
        # Simulation settings
        self.sim.dt = 0.005
        self.scene.contact_forces.update_period = self.sim.dt
        self.sim.render_interval = self.decimation
        self.sim.physx.bounce_threshold_velocity = 0.01
        self.sim.physx.gpu_found_lost_aggregate_pairs_capacity = 1024 * 1024 * 4
        self.sim.physx.gpu_total_aggregate_pairs_capacity = 16 * 1024
        self.sim.physx.friction_correlation_distance = 0.00625
        
        # Physics material properties
        self.sim.physics_material.static_friction = 1.0
        self.sim.physics_material.dynamic_friction = 1.0
        self.sim.physics_material.friction_combine_mode = "max"
        self.sim.physics_material.restitution_combine_mode = "max"

