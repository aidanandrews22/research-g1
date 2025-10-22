# CUDA_VISIBLE_DEVICES=1 python scripts/inference_service_g1.py --server --model-path /home/aidan/checkpoints/unitree-g1-finetune/ --data-config unitree_g1 --embodiment-tag new_embodiment

"""
GR00T Inference Service

This script provides both ZMQ and HTTP server/client implementations for deploying GR00T models.
The HTTP server exposes a REST API for easy integration with web applications and other services.

1. Default is zmq server.

Run server: python scripts/inference_service.py --server
Run client: python scripts/inference_service.py --client

2. Run as Http Server:

Dependencies for `http_server` mode:
    => Server (runs GR00T model on GPU): `pip install uvicorn fastapi json-numpy`
    => Client: `pip install requests json-numpy`

HTTP Server Usage:
    python scripts/inference_service.py --server --http-server --port 8000

HTTP Client Usage (assuming a server running on 0.0.0.0:8000):
    python scripts/inference_service.py --client --http-server --host 0.0.0.0 --port 8000

You can use bore to forward the port to your client: `159.223.171.199` is bore.pub.
    bore local 8000 --to 159.223.171.199
"""

import time
import json
from dataclasses import dataclass
from typing import Literal
from pathlib import Path
from datetime import datetime
import threading
from queue import Queue

import numpy as np
import tyro

from gr00t.data.embodiment_tags import EMBODIMENT_TAG_MAPPING
from gr00t.eval.robot import RobotInferenceClient, RobotInferenceServer
from gr00t.experiment.data_config import load_data_config
from gr00t.model.policy import Gr00tPolicy


@dataclass
class ArgsConfig:
    """Command line arguments for the inference service."""

    model_path: str = "nvidia/GR00T-N1.5-3B"
    """Path to the model checkpoint directory."""

    embodiment_tag: Literal[tuple(EMBODIMENT_TAG_MAPPING.keys())] = "gr1"
    """The embodiment tag for the model."""

    data_config: str = "fourier_gr1_arms_waist"
    """
    The name of the data config to use, e.g. so100, fourier_gr1_arms_only, unitree_g1, etc.

    Or a path to a custom data config file. e.g. "module:ClassName" format.
    See gr00t/experiment/data_config.py for more details.
    """

    port: int = 5555
    """The port number for the server."""

    host: str = "localhost"
    """The host address for the server."""

    server: bool = False
    """Whether to run the server."""

    client: bool = False
    """Whether to run the client."""

    denoising_steps: int = 4
    """The number of denoising steps to use."""

    api_token: str = None
    """API token for authentication. If not provided, authentication is disabled."""

    http_server: bool = False
    """Whether to run it as HTTP server. Default is ZMQ server."""

    log_dir: str = "logs/groot_server"
    """Directory to save input/output logs."""


#####################################################################################


class LoggingRobotInferenceServer(RobotInferenceServer):
    """Simple server that logs directly in the request loop."""
    
    def __init__(self, model, host: str = "*", port: int = 5555, api_token: str = None, log_dir: str = "logs/groot_server"):
        super().__init__(model, host, port, api_token)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.image_dir = self.log_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.log_file = self.log_dir / f"server_log_{timestamp}.jsonl"
        self.step_count = 0
        
        print(f"[SERVER LOG] Logging to {self.log_file}")
        print(f"[SERVER LOG] Saving images to {self.image_dir}")
    
    def run(self):
        """Override run to add inline logging."""
        from gr00t.eval.service import MsgSerializer
        import zmq
        
        addr = self.socket.getsockopt_string(zmq.LAST_ENDPOINT)
        print(f"Server is ready and listening on {addr}")
        
        while self.running:
            try:
                message = self.socket.recv()
                request = MsgSerializer.from_bytes(message)
                
                if not self._validate_token(request):
                    self.socket.send(MsgSerializer.to_bytes({"error": "Unauthorized: Invalid API token"}))
                    continue
                
                endpoint = request.get("endpoint", "get_action")
                
                if endpoint not in self._endpoints:
                    raise ValueError(f"Unknown endpoint: {endpoint}")
                
                # Log and process get_action requests
                if endpoint == "get_action":
                    self.step_count += 1
                    obs = request.get("data", {})
                    
                    # Log input
                    input_log = {"step": self.step_count, "timestamp": datetime.now().isoformat(), "type": "input", "observation": {}}
                    for key, value in obs.items():
                        if isinstance(value, np.ndarray):
                            input_log["observation"][key] = {
                                "shape": list(value.shape), "dtype": str(value.dtype),
                                "min": float(np.min(value)), "max": float(np.max(value)),
                                "mean": float(np.mean(value)), "data": value.tolist()
                            }
                        else:
                            input_log["observation"][key] = value if isinstance(value, list) else str(value)
                    
                    # Save image
                    for key, value in obs.items():
                        if 'video' in key.lower() and isinstance(value, np.ndarray) and value.ndim >= 3:
                            img_data = value[0] if value.ndim == 4 else value
                            try:
                                from PIL import Image
                                Image.fromarray(img_data.astype(np.uint8)).save(self.image_dir / f"step_{self.step_count:06d}.png")
                            except:
                                np.save(self.image_dir / f"step_{self.step_count:06d}.npy", img_data)
                            break
                    
                    # Get action
                    handler = self._endpoints[endpoint]
                    time_start = time.time()
                    result = handler.handler(obs)
                    inference_time = time.time() - time_start
                    
                    # Log output
                    output_log = {"step": self.step_count, "timestamp": datetime.now().isoformat(), "type": "output", "inference_time": inference_time, "action": {}}
                    for key, value in result.items():
                        if isinstance(value, np.ndarray):
                            output_log["action"][key] = {
                                "shape": list(value.shape), "dtype": str(value.dtype),
                                "min": float(np.min(value)), "max": float(np.max(value)),
                                "mean": float(np.mean(value)), "data": value.tolist()
                            }
                    
                    # Write logs
                    with open(self.log_file, 'a') as f:
                        f.write(json.dumps(input_log) + '\n')
                        f.write(json.dumps(output_log) + '\n')
                    
                    print(f"[SERVER LOG] Step {self.step_count}: Inference {inference_time:.3f}s")
                else:
                    # Other endpoints
                    handler = self._endpoints[endpoint]
                    result = handler.handler(request.get("data", {})) if handler.requires_input else handler.handler()
                
                self.socket.send(MsgSerializer.to_bytes(result))
            except Exception as e:
                print(f"Error in server: {e}")
                import traceback
                traceback.print_exc()
                self.socket.send(MsgSerializer.to_bytes({"error": str(e)}))


#####################################################################################


def _example_zmq_client_call(obs: dict, host: str, port: int, api_token: str):
    """
    Example ZMQ client call to the server.
    """
    # Original ZMQ client mode
    # Create a policy wrapper
    policy_client = RobotInferenceClient(host=host, port=port, api_token=api_token)

    print("Available modality config available:")
    modality_configs = policy_client.get_modality_config()
    print(modality_configs.keys())

    time_start = time.time()
    print(f"Sending observation to server: {obs}")
    action = policy_client.get_action(obs)
    print(f"Total time taken to get action from server: {time.time() - time_start} seconds")
    return action


def _example_http_client_call(obs: dict, host: str, port: int, api_token: str):
    """
    Example HTTP client call to the server.
    """
    import json_numpy

    json_numpy.patch()
    import requests

    # Send request to HTTP server
    print("Testing HTTP server...")

    time_start = time.time()
    response = requests.post(f"http://{host}:{port}/act", json={"observation": obs})
    print(f"Total time taken to get action from HTTP server: {time.time() - time_start} seconds")

    if response.status_code == 200:
        action = response.json()
        return action
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return {}


def main(args: ArgsConfig):
    if args.server:
        # Create a policy
        # The `Gr00tPolicy` class is being used to create a policy object that encapsulates
        # the model path, transform name, embodiment tag, and denoising steps for the robot
        # inference system. This policy object is then utilized in the server mode to start
        # the Robot Inference Server for making predictions based on the specified model and
        # configuration.

        # we will use an existing data config to create the modality config and transform
        # if a new data config is specified, this expect user to
        # construct your own modality config and transform
        # see gr00t/utils/data.py for more details
        data_config = load_data_config(args.data_config)
        modality_config = data_config.modality_config()
        modality_transform = data_config.transform()

        policy = Gr00tPolicy(
            model_path=args.model_path,
            modality_config=modality_config,
            modality_transform=modality_transform,
            embodiment_tag=args.embodiment_tag,
            denoising_steps=args.denoising_steps,
        )

        # Start the server
        if args.http_server:
            from gr00t.eval.http_server import HTTPInferenceServer  # noqa: F401

            server = HTTPInferenceServer(
                policy, port=args.port, host=args.host, api_token=args.api_token
            )
            server.run()
        else:
            server = LoggingRobotInferenceServer(policy, port=args.port, api_token=args.api_token, log_dir=args.log_dir)
            server.run()

    # Here is mainly a testing code
    elif args.client:
        # In this mode, we will send a random observation to the server and get an action back
        # This is useful for testing the server and client connection

        # Making prediction...
        # - obs: video.rs_view: (1, 480, 640, 3)
        # - obs: state.left_arm: (1, 7)
        # - obs: state.right_arm: (1, 7)
        # - obs: state.left_hand: (1, 7)
        # - obs: state.right_hand: (1, 7)

        # - action: action.left_arm: (16, 7)
        # - action: action.right_arm: (16, 7)
        # - action: action.left_hand: (16, 7)
        # - action: action.right_hand: (16, 7)
        obs = {
            "video.rs_view": np.random.randint(0, 256, (1, 480, 640, 3), dtype=np.uint8),
            "state.left_arm": np.random.rand(1, 7),
            "state.right_arm": np.random.rand(1, 7),
            "state.left_hand": np.random.rand(1, 7),
            "state.right_hand": np.random.rand(1, 7),
            "annotation.human.task_description": ["do your thing!"],
        }

        if args.http_server:
            action = _example_http_client_call(obs, args.host, args.port, args.api_token)
        else:
            action = _example_zmq_client_call(obs, args.host, args.port, args.api_token)

        for key, value in action.items():
            print(f"Action: {key}: {value.shape}")
    else:
        raise ValueError("Please specify either --server or --client")


if __name__ == "__main__":
    config = tyro.cli(ArgsConfig)
    main(config)
