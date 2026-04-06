#!/usr/bin/env python3
"""Cross-platform setup: create venv + install deps."""
import os
import subprocess
import sys
import shutil

def main():
    plugin_data = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    plugin_root = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))

    venv_path = os.path.join(plugin_data, ".venv")
    req_src = os.path.join(plugin_root, "requirements.txt")
    req_cache = os.path.join(plugin_data, "requirements.txt")

    # Skip if venv exists and requirements unchanged
    if os.path.isdir(venv_path):
        try:
            with open(req_src) as a, open(req_cache) as b:
                if a.read() == b.read():
                    return  # already up to date
        except FileNotFoundError:
            pass

    print("[lollipop-mcp] Setting up Python venv...")
    subprocess.check_call([sys.executable, "-m", "venv", venv_path])

    # pip path differs on Windows vs Unix
    if sys.platform == "win32":
        pip = os.path.join(venv_path, "Scripts", "pip")
    else:
        pip = os.path.join(venv_path, "bin", "pip")

    subprocess.check_call([pip, "install", "-q", "-r", req_src])
    if os.path.abspath(req_src) != os.path.abspath(req_cache):
        shutil.copy2(req_src, req_cache)
    print("[lollipop-mcp] Setup complete.")

if __name__ == "__main__":
    main()
