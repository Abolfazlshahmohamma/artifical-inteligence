import sys
import os
import time
import threading
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger
from config import Config
from agent import WakeUpAgent
from cli.wake_listener import WakeListener
from gui.app import ModernGUI
from ipc.server import IPCServer

logger = get_logger("main")

def on_activation_phrase():
    """Callback when 'its time to wake up' is typed anywhere."""
    logger.info("Activation phrase detected! Waking up...")
    
    if hasattr(main, "_gui") and main._gui:
        main._gui.show()
        main._gui.add_message("system", "Activation phrase detected. Agent is now active.")
        main._gui._update_status("active")
    
    if hasattr(main, "_agent") and main._agent:
        main._agent.activate()

def on_ipc_message(message: str):
    """Callback for IPC messages."""
    logger.info(f"IPC message received: {message}")
    
    if message.lower() in ("activate", "wake", "wakeup", "wake up", "its time to wake up"):
        on_activation_phrase()
    elif message.lower() in ("deactivate", "sleep"):
        if hasattr(main, "_agent") and main._agent:
            main._agent.deactivate()
            if hasattr(main, "_gui") and main._gui:
                main._gui.hide()

class MainDaemon:
    """Main daemon that orchestrates the agent, keyboard hook, IPC, and GUI."""
    
    def __init__(self):
        self._agent = None
        self._gui = None
        self._keyboard_hook = None
        self._ipc_server = None
        self._running = False
    
    def start(self, immediate_activate: bool = False):
        logger.info("Starting WakeUp Agent daemon...")
        
        Config.reload()
        
        self._agent = WakeUpAgent()
        if not self._agent.initialize():
            logger.error("Failed to initialize agent")
        
        activation_phrase = Config.get("activation_phrase", "its time to wake up")
        self._keyboard_hook = WakeListener(
            activation_phrase=activation_phrase,
            callback=on_activation_phrase
        )
        
        self._ipc_server = IPCServer(on_message=on_ipc_message)
        
        self._running = True
        
        keyboard_thread = threading.Thread(target=self._keyboard_hook.start, daemon=True)
        keyboard_thread.start()
        logger.info(f"Keyboard hook thread started. Listening for: '{activation_phrase}'")
        
        self._ipc_server.start()
        logger.info("IPC server started")
        
        self._gui = ModernGUI(
            agent=self._agent,
            width=Config.get("gui.window_size", [480, 720])[0],
            height=Config.get("gui.window_size", [480, 720])[1]
        )
        
        if immediate_activate:
            self._agent.activate()
            self._gui._update_status("active")
        
        def _hide_initially():
            time.sleep(2)
            if not self._agent._active:
                self._gui.hide()
        
        threading.Thread(target=_hide_initially, daemon=True).start()
        
        logger.info("GUI initialized, starting main loop")
        self._gui.run()
        
        self._running = False
        self._cleanup()
    
    def _cleanup(self):
        logger.info("Cleaning up...")
        if self._keyboard_hook:
            self._keyboard_hook.stop()
        if self._ipc_server:
            self._ipc_server.stop()
        if self._agent:
            self._agent.stop_listening()
        logger.info("Cleanup complete")

main = MainDaemon()

if __name__ == "__main__":
    immediate = "--activate" in sys.argv
    main.start(immediate_activate=immediate)
