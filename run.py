#!/usr/bin/env python3
"""Cross-platform launcher: find venv python, exec mcp_hub.py."""
import os
import subprocess
import sys

def main():
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", os.path.dirname(os.path.abspath(__file__)))
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.abspath(__file__)))

    venv_path = os.path.join(plugin_data, ".venv")

    if sys.platform == "win32":
        python = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python = os.path.join(venv_path, "bin", "python3")

    if not os.path.isfile(python):
        # Run setup first
        setup = os.path.join(plugin_root, "setup.py")
        subprocess.check_call([sys.executable, setup, plugin_data, plugin_root])

    hub = os.path.join(plugin_root, "mcp_hub.py")
    os.execv(python, [python, hub])

if __name__ == "__main__":
    main()
