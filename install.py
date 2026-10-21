#!/usr/bin/env python
"""
WakeUp Agent Installation Script
Sets up the agent for automatic startup and cmd activation.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
SCRIPT_NAME = "wakeup"
ACTIVATION_PHRASE = "its time to wake up"

def install():
    print("=" * 60)
    print("  WakeUp Agent - Installation")
    print("=" * 60)
    print()
    
    app_path = str(BASE_DIR / "main.py")
    python_exe = sys.executable
    
    print(f"[1/5] Checking Python: {python_exe}")
    print(f"      Project path: {BASE_DIR}")
    print()
    
    print("[2/5] Creating activation batch file...")
    batch_content = f"""@echo off
python "{BASE_DIR}\\main.py" --activate
"""
    batch_path = BASE_DIR / "wakeup.bat"
    batch_path.write_text(batch_content)
    print(f"      Created: {batch_path}")
    print()
    
    print("[3/5] Adding to System PATH...")
    current_path = os.environ.get("PATH", "")
    if str(BASE_DIR) not in current_path:
        os.system(f'setx PATH "{current_path};{BASE_DIR}"')
        print(f"      Added {BASE_DIR} to PATH")
    else:
        print(f"      Already in PATH")
    print()
    
    print("[4/5] Creating doskey alias for cmd...")
    doskey_content = [
        'doskey its time to wake up=python -c "import os; os.system(\'start /min python \\\"{}\\\\main.py\\\" --activate\')"'.format(BASE_DIR),
        'doskey wake=python "{}\\cli\\activate.py"'.format(BASE_DIR),
    ]
    
    profile_content = f"""
REM WakeUp Agent Aliases
REM Type 'wake' in cmd to activate the agent
REM Type the full phrase 'its time to wake up' to trigger activation
doskey wake={"python" if False else python_exe} "{BASE_DIR}\\cli\\activate.py"
doskey wakeup={"python" if False else python_exe} "{BASE_DIR}\\main.py" --activate
"""
    
    app_data = os.environ.get("APPDATA", "")
    if app_data:
        profile_path = Path(app_data) / ".." / "Local\\Microsoft\\WindowsApps"
        cmd_profile = Path(app_data) / "Microsoft\\Windows\\Start Menu\\Programs\\Startup\\wakeup_agent.bat"
        
        startup_dir = Path(os.environ.get("APPDATA", "")) / ".." / "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        startup_dir.mkdir(parents=True, exist_ok=True)
        
        startup_script = startup_dir / "wakeup_agent.bat"
        startup_script.write_text(f'@echo off\nstart /min "{python_exe}" "{app_path}"\n')
        print(f"      Created startup script: {startup_script}")
    
    print()
    
    print("[5/5] Creating desktop shortcut...")
    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if desktop.exists():
        shortcut_path = desktop / "WakeUp Agent.exe"
        vbs_content = f"""
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python -u """ + str(app_path) + """", 0, False
"""
        vbs_path = desktop / "WakeUp Agent.vbs"
        vbs_path.write_text(vbs_content)
        print(f"      Created: {vbs_path}")
    print()
    
    print("=" * 60)
    print("  Installation Complete!")
    print("=" * 60)
    print()
    print("  To activate the agent:")
    print("  1. Type 'wake' in cmd, OR")
    print(f"  2. Type the full phrase: '{ACTIVATION_PHRASE}' anywhere")
    print()
    print("  To configure API keys:")
    print("  Edit config.json in the project directory")
    print()
    print("  To run now (test mode):")
    print(f"    python \"{app_path}\"")
    print()

def setup_config():
    """Interactive setup for API keys."""
    print("\n" + "=" * 60)
    print("  Configuration Setup")
    print("=" * 60)
    
    config_path = BASE_DIR / "config.json"
    
    print("\n  [API Keys]")
    print("  Enter your API keys below. Leave empty to skip.")
    print("  (These can be edited later in config.json)\n")
    
    import json
    config = {}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    
    print("  OpenRouter API Key (for AI models):")
    print("  Get one at: https://openrouter.ai/keys")
    openrouter_key = input("  > ").strip()
    if openrouter_key:
        config.setdefault("llm", {})["api_key"] = openrouter_key
        config.setdefault("llm", {})["provider"] = "openrouter"
    
    print("\n  GitHub Token (for GitHub integration):")
    print("  Get one at: https://github.com/settings/tokens")
    github_token = input("  > ").strip()
    if github_token:
        config.setdefault("github", {})["token"] = github_token
    
    print("\n  GitHub Username:")
    github_user = input("  > ").strip()
    if github_user:
        config.setdefault("github", {})["username"] = github_user
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    print("\n  Configuration saved to config.json")
    print()

if __name__ == "__main__":
    install()
    
    if "--setup" in sys.argv:
        setup_config()
    else:
        print("Run with --setup flag for interactive API key configuration.")
