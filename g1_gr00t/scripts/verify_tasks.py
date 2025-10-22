#!/usr/bin/env python3
"""Quick verification that both tasks have identical structure, with Isaac AppLauncher."""

import argparse
import sys

# Import the Isaac AppLauncher *before* any isaac/omni imports
from isaaclab.app import AppLauncher

# -----------------------------------------------------------------------------
# Parse CLI arguments (including AppLauncher’s own)
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Compare two Isaac Lab task EnvCfg classes.")
AppLauncher.add_app_launcher_args(parser)
parser.add_argument(
    "--cylinder",
    default="g1_gr00t.tasks.move_cylinder.env_cfg.MoveCylinderEnvCfg",
    help="Fully-qualified path to the first EnvCfg class.",
)
parser.add_argument(
    "--nutpour",
    default="g1_gr00t.tasks.nutpour.env_cfg.NutPourEnvCfg",
    help="Fully-qualified path to the second EnvCfg class.",
)
args_cli = parser.parse_args()

# -----------------------------------------------------------------------------
# Launch the simulator context (headless, lightweight)
# -----------------------------------------------------------------------------
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Now Isaac packages (isaaclab, omni.isaac, etc.) are importable
import importlib

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def import_class(path: str):
    mod, _, cls = path.rpartition(".")
    module = importlib.import_module(mod)
    return getattr(module, cls)

def safe_get(obj, path):
    for part in path.split("."):
        if not hasattr(obj, part):
            return None
        obj = getattr(obj, part)
    return obj

def fmt(v):
    return str(v) if v is not None else "—"

# -----------------------------------------------------------------------------
# Load and compare EnvCfgs
# -----------------------------------------------------------------------------
try:
    CylCls = import_class(args_cli.cylinder)
    NutCls = import_class(args_cli.nutpour)
    print("✅ Imported both EnvCfg classes successfully.\n")

    cyl = CylCls()
    nut = NutCls()
    print("✅ Instantiated both EnvCfgs.\n")
except Exception as e:
    print(f"❌ Failed to import or instantiate configs: {e}")
    simulation_app.close()
    sys.exit(1)

settings = [
    "decimation",
    "episode_length_s",
    "sim.dt",
    "scene.num_envs",
    "scene.env_spacing",
]

print("=" * 72)
print("CONFIGURATION COMPARISON")
print("=" * 72)
print(f"{'Setting':<32} {'Cylinder':<18} {'NutPour':<18} {'Match'}")
print("-" * 72)

all_match = True
for path in settings:
    cval = safe_get(cyl, path)
    nval = safe_get(nut, path)
    match = "✅" if cval == nval else "❌"
    if cval != nval:
        all_match = False
    print(f"{path:<32} {fmt(cval):<18} {fmt(nval):<18} {match}")

print("-" * 72)
print("\nMANAGER CONFIGURATION")
print("=" * 72)
print(f"{'Manager':<20} {'Cylinder':<18} {'NutPour':<18} {'Match'}")
print("-" * 72)
for name in ["observations", "actions", "rewards", "terminations", "events"]:
    c_has = hasattr(cyl, name)
    n_has = hasattr(nut, name)
    match = "✅" if c_has == n_has else "❌"
    if c_has != n_has:
        all_match = False
    print(f"{name:<20} {str(c_has):<18} {str(n_has):<18} {match}")
print("-" * 72)

print("\n" + "=" * 72)
if all_match:
    print("✅ ALL SETTINGS MATCH - Tasks are structurally identical!")
else:
    print("❌ MISMATCH DETECTED - Review differences above")
print("=" * 72)

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
simulation_app.close()
sys.exit(0 if all_match else 1)

