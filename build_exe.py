import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Collect items to include
add_data_args = []
for item in os.listdir(BASE_DIR):
    item_path = os.path.join(BASE_DIR, item)
    # Skip python scripts, workspace, pycache, build output, etc.
    if item.endswith(".py") or item.endswith(".code-workspace") or item in [".vscode", ".git", "build", "dist", "color_pentagon.spec", ".gemini"]:
        continue
        
    if os.path.isdir(item_path):
        add_data_args.extend(["--add-data", f"{item};{item}"])
    elif os.path.isfile(item_path):
        # Including individual images if needed, but usually champions are in folders
        if item.endswith(".png") or item.endswith(".md"):
            add_data_args.extend(["--add-data", f"{item};."])

# PyInstaller command
cmd = [
    "pyinstaller",
    "--noconsole",
    "--onefile",
    "--name", "ColorPentagon",
    "color_pentagon.py"
]

cmd.extend(add_data_args)

print("Starting build...")
print(f"Command: {' '.join(cmd[:10])} ... (truncated)")

result = subprocess.run(cmd, shell=True)
if result.returncode == 0:
    print("Build successful! Exe is in the 'dist' folder.")
else:
    print("Build failed.")
