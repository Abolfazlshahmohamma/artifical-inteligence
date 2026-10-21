#!/usr/bin/env python
"""Quick run script for testing the WakeUp Agent."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger
from agent import WakeUpAgent
from gui.app import ModernGUI
from config import Config
import threading
import time

logger = get_logger("run")

def test_mode():
    """Run the agent in test mode (no keyboard hook, GUI only)."""
    logger.info("Starting in test mode...")
    
    Config.reload()
    
    agent = WakeUpAgent()
    agent.initialize()
    
    gui = ModernGUI(agent=agent, width=480, height=720)
    
    agent.add_listener(lambda event: gui.add_message("system", f"Event: {event}"))
    
    gui._add_message("system", "Agent initialized in test mode.")
    gui._add_message("system", "Click the mic button or type a command to start.")
    gui._add_message("system", f"Skills loaded: {len(agent.skills.skills)}")
    gui._update_status("active")
    
    agent.activate()
    
    gui.run()

def gui_test():
    """Just test the GUI."""
    logger.info("Starting GUI test mode...")
    
    class DummyLLM:
        model = "google/gemini-2.5-flash"
        provider = "openrouter"
    
    class DummyAgent:
        llm = DummyLLM()
        
        def get_status(self):
            return {
                "active": True,
                "paused": False,
                "skills_count": 0,
                "github_connected": False,
                "tts_ready": True,
                "stt_backend": "windows_sapi",
                "llm_provider": "openrouter",
                "llm_model": "google/gemini-2.5-flash",
                "conversation_length": 0,
                "local_model_enabled": False
            }
        
        def process_command(self, text):
            return f"Echo: {text}"
        
        _active = True
        _paused = False
        
        def activate(self):
            pass
        
        def deactivate(self):
            pass
    
    gui = ModernGUI(agent=DummyAgent(), width=480, height=720)
    gui._add_message("system", "GUI Test Mode")
    gui._add_message("agent", "This is a test message from the agent.")
    gui._add_message("user", "This is a test message from the user.")
    gui._update_status("active")
    gui.run()

def voice_test():
    """Test voice input/output."""
    logger.info("Starting voice test...")
    
    from voice.tts import TTS
    from voice.stt import STT
    
    tts = TTS()
    tts.speak("Hello, I am WakeUp Agent. Voice test complete.")
    
    stt = STT(backend="windows_sapi")
    print("Listening for 10 seconds... Speak now.")
    text = stt.listen(timeout=10)
    print(f"Recognized: {text}")

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if "--gui-test" in args:
        gui_test()
    elif "--voice-test" in args:
        voice_test()
    elif "--test" in args:
        test_mode()
    else:
        print("WakeUp Agent")
        print("Usage:")
        print("  python run.py --test       : Full test mode (agent + GUI)")
        print("  python run.py --gui-test   : GUI test only")
        print("  python run.py --voice-test : Voice test only")
        print("  python run.py              : Show this help")
