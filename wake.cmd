@echo off
REM WakeUp Agent - Activation script
REM Usage: type "wake" in cmd to activate the agent
REM Or type the full phrase "its time to wake up" anywhere

python -c "import sys; sys.path.insert(0, r'%~dp0'); from cli.activate import activate_agent; activate_agent()"
