# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Camera configurations for G1 robot observations."""

import isaaclab.sim as sim_utils
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass


@configclass
class CameraBaseCfg:
    """Base camera configuration with common parameters."""
    
    @classmethod
    def get_camera_config(
        cls,
        prim_path: str = "/World/envs/env_.*/Robot/d435_link/front_cam",
        update_period: float = 0.02,
        height: int = 480,
        width: int = 640,
        focal_length: float = 7.6,
        focus_distance: float = 400.0,
        horizontal_aperture: float = 20.0,
        clipping_range: tuple = (0.1, 1.0e5),
        pos_offset: tuple = (0, 0.0, 0),
        rot_offset: tuple = (0.5, -0.5, 0.5, -0.5),
        data_types: list = None
    ) -> CameraCfg:
        """Create camera configuration with specified parameters.
        
        Args:
            prim_path: Camera path in the scene
            update_period: Update period (seconds)
            height: Image height (pixels)
            width: Image width (pixels)
            focal_length: Focal length
            focus_distance: Focus distance
            horizontal_aperture: Horizontal aperture
            clipping_range: Clipping range (near, far)
            pos_offset: Position offset (x, y, z)
            rot_offset: Rotation offset quaternion
            data_types: Data types to capture
            
        Returns:
            CameraCfg: Camera configuration
        """
        if data_types is None:
            data_types = ["rgb"]

        return CameraCfg(
            prim_path=prim_path,
            update_period=update_period,
            height=height,
            width=width,
            data_types=data_types,
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=focal_length,
                focus_distance=focus_distance,
                horizontal_aperture=horizontal_aperture,
                clipping_range=clipping_range
            ),
            offset=CameraCfg.OffsetCfg(
                pos=pos_offset,
                rot=rot_offset,
                convention="ros"
            )
        )


@configclass
class CameraPresets:
    """Preset camera configurations for G1 robot."""
    
    @classmethod
    def g1_front_camera(cls) -> CameraCfg:
        """Front-facing camera on robot head."""
        return CameraBaseCfg.get_camera_config()
    
    @classmethod
    def g1_world_camera(cls) -> CameraCfg:
        """Third-person view camera following robot."""
        return CameraBaseCfg.get_camera_config(
            prim_path="/World/envs/env_.*/Robot/d435_link/PerspectiveCamera_robot",
            pos_offset=(-0.9, 0.0, 0.0),
            rot_offset=(-0.51292, 0.51292, -0.48674, 0.48674),
            focal_length=12,
            horizontal_aperture=27
        )
    
    @classmethod
    def left_dex3_wrist_camera(cls) -> CameraCfg:
        """Camera on left Dex3 hand wrist."""
        return CameraBaseCfg.get_camera_config(
            prim_path="/World/envs/env_.*/Robot/left_hand_camera_base_link/left_wrist_camera",
            height=480,
            width=640,
            update_period=0.02,
            data_types=["rgb"],
            focal_length=12.0,
            focus_distance=400.0,
            horizontal_aperture=20.0,
            clipping_range=(0.1, 1.0e5),
            pos_offset=(-0.04012, -0.07441, 0.15711),
            rot_offset=(0.00539, 0.86024, 0.0424, 0.50809),
        )
    
    @classmethod
    def right_dex3_wrist_camera(cls) -> CameraCfg:
        """Camera on right Dex3 hand wrist."""
        return CameraBaseCfg.get_camera_config(
            prim_path="/World/envs/env_.*/Robot/right_hand_camera_base_link/right_wrist_camera",
            height=480,
            width=640,
            update_period=0.02,
            data_types=["rgb"],
            focal_length=12.0,
            focus_distance=400.0,
            horizontal_aperture=20.0,
            clipping_range=(0.1, 1.0e5),
            pos_offset=(-0.04012, 0.07441, 0.15711),
            rot_offset=(0.00539, 0.86024, 0.0424, 0.50809),
        )

