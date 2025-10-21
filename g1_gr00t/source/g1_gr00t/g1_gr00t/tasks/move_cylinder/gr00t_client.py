# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

"""GR00T N1.5 client for G1 robot control."""

import torch
import numpy as np
import zmq
import msgpack
import io
from typing import Dict, Any, Optional


class MsgSerializer:
    """Message serializer compatible with GR00T server."""
    
    @staticmethod
    def to_bytes(data: dict) -> bytes:
        return msgpack.packb(data, default=MsgSerializer.encode_custom_classes)
    
    @staticmethod
    def from_bytes(data: bytes) -> dict:
        return msgpack.unpackb(data, object_hook=MsgSerializer.decode_custom_classes)
    
    @staticmethod
    def decode_custom_classes(obj):
        if "__ndarray_class__" in obj:
            obj = np.load(io.BytesIO(obj["as_npy"]), allow_pickle=False)
        return obj
    
    @staticmethod
    def encode_custom_classes(obj):
        if isinstance(obj, np.ndarray):
            buffer = io.BytesIO()
            np.save(buffer, obj, allow_pickle=False)
            return {"__ndarray_class__": True, "as_npy": buffer.getvalue()}
        return obj


class GR00TClient:
    """Client to communicate with GR00T N1.5 inference server via ZMQ.
    
    GR00T expects:
    - video.rs_view: (H, W, 3) uint8 image
    - state.left_arm: 7 joint values (shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll, wrist_pitch, wrist_yaw)
    - state.right_arm: 7 joint values
    - state.left_hand: 7 Dex3 hand joint values
    - state.right_hand: 7 Dex3 hand joint values
    - annotation.human.task_description: text string
    
    GR00T returns:
    - action.left_arm: (n_timesteps, 7)
    - action.right_arm: (n_timesteps, 7)
    - action.left_hand: (n_timesteps, 7)
    - action.right_hand: (n_timesteps, 7)
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5555,
        n_timesteps: int = 16,
        task_description: str = "pick up the cylinder",
    ):
        self.host = host
        self.port = port
        self.n_timesteps = n_timesteps
        self.task_description = task_description
        self._connected = False
        self._socket = None
        self._context = None
        self._action_queue = []  # Queue to store predicted actions
        self._current_timestep = 0
        
        # Joint indices for our 43 DOF robot (from modality.json)
        # state indices: [0-6: left_leg, 6-12: right_leg, 12-15: waist, 
        #                 15-22: left_arm, 22-29: left_hand, 29-36: right_arm, 36-43: right_hand]
        self.left_arm_indices = list(range(15, 22))    # 7 joints
        self.right_arm_indices = list(range(29, 36))   # 7 joints
        self.left_hand_indices = list(range(22, 29))   # 7 joints
        self.right_hand_indices = list(range(36, 43))  # 7 joints

    def connect(self):
        """Connect to GR00T server via ZMQ."""
        try:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.connect(f"tcp://{self.host}:{self.port}")
            self._socket.setsockopt(zmq.RCVTIMEO, 10000)  # 10 second timeout
            self._connected = True
            print(f"[GR00T] Connected to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"[GR00T] Failed to connect: {e}")
            self._connected = False

    def disconnect(self):
        """Disconnect from GR00T server."""
        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()
        self._connected = False
        print("[GR00T] Disconnected from server")

    def _prepare_observation(self, obs: Dict[str, torch.Tensor], env) -> Dict[str, np.ndarray]:
        """Convert Isaac Lab observation to GR00T format.
        
        Args:
            obs: Observation dict from Isaac Lab with keys 'robot_body_state', 'robot_hand_state'
            env: Environment instance (to access cameras)
            
        Returns:
            Dict in GR00T format
        """
        # Get joint states (87 values: 29 joints * 3 for pos/vel/torque)
        body_state = obs['robot_body_state'][0].cpu().numpy()  # (87,)
        hand_state = obs['robot_hand_state'][0].cpu().numpy()  # (42,) = 14 joints * 3
        
        # Extract positions only (every 3rd value starting from 0)
        body_positions = body_state[::3]  # 29 positions
        hand_positions = hand_state[::3]  # 14 positions
        
        # Combine into full 43 DOF state and convert to float64
        full_state = np.concatenate([body_positions, hand_positions]).astype(np.float64)
        
        # Extract arm and hand states
        left_arm = full_state[self.left_arm_indices]
        right_arm = full_state[self.right_arm_indices]
        left_hand = full_state[self.left_hand_indices]
        right_hand = full_state[self.right_hand_indices]
        
        # Get camera image from front_camera
        image = None
        try:
            if hasattr(env.unwrapped.scene, 'sensors'):
                front_cam = env.unwrapped.scene.sensors.get('front_camera')
                if front_cam and hasattr(front_cam, 'data'):
                    rgb_data = front_cam.data.output.get('rgb')
                    if rgb_data is not None:
                        # Convert to numpy uint8
                        img_np = rgb_data[0].cpu().numpy()  # (H, W, 3)
                        if img_np.dtype != np.uint8:
                            image = (np.clip(img_np, 0, 1) * 255).astype(np.uint8)
                        else:
                            image = img_np
        except Exception as e:
            print(f"[GR00T] Warning: Could not get camera image: {e}")
        
        # Fallback to random image if camera not available
        if image is None:
            image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        return {
            'video.rs_view': image[np.newaxis, ...],  # Add batch dimension
            'state.left_arm': left_arm[np.newaxis, ...],
            'state.right_arm': right_arm[np.newaxis, ...],
            'state.left_hand': left_hand[np.newaxis, ...],
            'state.right_hand': right_hand[np.newaxis, ...],
            'annotation.human.task_description': [self.task_description],
        }

    def get_action(self, obs: Dict[str, torch.Tensor], env) -> torch.Tensor:
        """Get action from GR00T server.
        
        Args:
            obs: Observation dict from Isaac Lab
            env: Environment instance (to access cameras)
            
        Returns:
            Action tensor (28 DOF: 14 arm + 14 hand joint positions)
        """
        if not self._connected:
            print("[GR00T] Not connected. Returning zero actions.")
            return torch.zeros(28, dtype=torch.float32)
        
        # If we have actions in queue, use those first
        if self._action_queue and self._current_timestep < len(self._action_queue):
            action = self._action_queue[self._current_timestep]
            self._current_timestep += 1
            return torch.from_numpy(action).float()
        
        # Need to query GR00T for new actions
        try:
            # Prepare observation
            groot_obs = self._prepare_observation(obs, env)
            
            # Prepare request in GR00T format
            request = {
                "endpoint": "get_action",
                "data": groot_obs
            }
            
            # Send to server
            self._socket.send(MsgSerializer.to_bytes(request))
            
            # Receive response
            message = self._socket.recv()
            response = MsgSerializer.from_bytes(message)
            
            # Check for error
            if "error" in response:
                raise RuntimeError(f"Server error: {response['error']}")
            
            actions_dict = response
            
            # Extract actions: (n_timesteps, 7) for each part
            left_arm_actions = actions_dict['action.left_arm']    # (16, 7)
            right_arm_actions = actions_dict['action.right_arm']  # (16, 7)
            left_hand_actions = actions_dict['action.left_hand']  # (16, 7)
            right_hand_actions = actions_dict['action.right_hand']  # (16, 7)
            
            # Reconstruct 28 DOF actions for each timestep (arms and hands only)
            # Action space order: left_arm(7), right_arm(7), left_hand(7), right_hand(7)
            self._action_queue = []
            for t in range(left_arm_actions.shape[0]):
                # Concatenate arm and hand actions (28 DOF total)
                action_28dof = np.concatenate([
                    left_arm_actions[t],   # 7 DOF
                    right_arm_actions[t],  # 7 DOF
                    left_hand_actions[t],  # 7 DOF
                    right_hand_actions[t], # 7 DOF
                ], dtype=np.float32)
                
                self._action_queue.append(action_28dof)
            
            # Return first action
            self._current_timestep = 1
            print(f"[GR00T] Received {len(self._action_queue)} timesteps of actions")
            return torch.from_numpy(self._action_queue[0]).float()
            
        except zmq.error.Again:
            print("[GR00T] Request timeout")
            return torch.zeros(28, dtype=torch.float32)
        except Exception as e:
            print(f"[GR00T] Error getting action: {e}")
            import traceback
            traceback.print_exc()
            return torch.zeros(28, dtype=torch.float32)

    def is_connected(self) -> bool:
        return self._connected


def create_groot_client(
    host: str = "localhost",
    port: int = 5555,
    task_description: str = "pick up the cylinder"
) -> GR00TClient:
    """Factory function to create GR00T client.
    
    Args:
        host: GR00T server host
        port: GR00T server port
        task_description: Task description for the robot
    
    Returns:
        GR00TClient: Client instance (not yet connected)
    """
    return GR00TClient(host=host, port=port, task_description=task_description)
