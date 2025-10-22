# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Task definitions for G1 GR00T project."""

# Import tasks to trigger gym registration
from . import move_cylinder  # noqa: F401
from . import nutpour  # noqa: F401

__all__ = ["move_cylinder", "nutpour"]
