import os
import sys
import json
import re
import subprocess
import threading
import time
from typing import Optional, List, Dict, Any, Tuple
from utils.logger import get_logger
from config import Config
from llm.client import LLMClient
from github_client import GitHubClient
from skills.engine import SkillsEngine
from voice.tts import TTS
from voice.stt import STT

logger = get_logger("agent")

class WakeUpAgent:
    """
    WakeUp Agent - The core orchestrator that ties together voice, LLM,
    GitHub integration, and skills execution.
    """
    
    def __init__(self):
        self.config = Config()
        self.llm = LLMClient()
        self.github = None
        self.skills = SkillsEngine()
        self.tts = TTS(
            voice=Config.get("tts_voice", ""),
            rate=Config.get("voice.rate", 0) if Config.get("voice.rate") else 0,
            volume=Config.get("voice.volume", 100) if Config.get("voice.volume") else 100
        )
        self.stt = STT(
            backend=Config.get("stt_backend", "windows_sapi"),
            language=Config.get("voice.language", "en-US")
        )
        
        self._active = False
        self._paused = False
        self._conversation_history: List[Dict[str, str]] = []
        self._max_history = 20
        self._listeners: List[callable] = []
        self._action_handlers: Dict[str, callable] = {}
        
        self._register_action_handlers()
    
    def initialize(self) -> bool:
        """Initialize the agent and all subsystems."""
        logger.info("Initializing WakeUp Agent...")
        
        token = Config.get("github.token", "")
        if token:
            self.github = GitHubClient()
            user = self.github.get_user()
            if user:
                logger.info(f"GitHub authenticated as: {user.get('login', 'unknown')}")
                Config.set("github.username", user.get("login", ""))
        
        self.skills.initialize()
        
        logger.info("WakeUp Agent initialized successfully")
        return True
    
    def _register_action_handlers(self):
        """Register handlers for different action types."""
        self._action_handlers = {
            "github_read": self._action_github_read,
            "github_write": self._action_github_write,
            "github_pr": self._action_github_pr,
            "skill": self._action_skill,
            "web_search": self._action_web_search,
            "file_read": self._action_file_read,
            "file_write": self._action_file_write,
            "shell": self._action_shell,
        }
    
    def activate(self):
        """Activate the agent (called when activation phrase is detected)."""
        self._active = True
        logger.info("Agent activated!")
        
        self._add_system_prompt()
        self.tts.speak("I'm awake. How can I help you?", async_mode=True)
        
        for listener in self._listeners:
            try:
                listener("activated")
            except Exception as e:
                logger.error(f"Error notifying listener: {e}")
    
    def deactivate(self):
        """Deactivate the agent."""
        self._active = False
        logger.info("Agent deactivated.")
    
    def add_listener(self, listener: callable):
        """Add a listener for agent events."""
        self._listeners.append(listener)
    
    def _add_system_prompt(self):
        """Add system prompt to conversation history."""
        if not self._conversation_history:
            self._conversation_history = [
                {"role": "system", "content": self.llm.get_system_prompt()}
            ]
    
    def _trim_history(self):
        """Keep conversation history within max length."""
        if len(self._conversation_history) > self._max_history:
            system = self._conversation_history[0] if self._conversation_history else None
            recent = self._conversation_history[-(self._max_history - 1):]
            if system:
                self._conversation_history = [system] + recent
            else:
                self._conversation_history = recent
    
    def process_command(self, command: str) -> str:
        """
        Process a user command (text) through the LLM and execute actions.
        
        Args:
            command: The user's input (from voice or text)
        
        Returns:
            The response text
        """
        logger.info(f"Processing command: {command[:100]}")
        
        self._add_system_prompt()
        self._conversation_history.append({"role": "user", "content": command})
        
        self._trim_history()
        
        context = self._build_context()
        full_prompt = f"Context:\n{context}\n\nUser: {command}\n\nAnalyze the request and determine what action to take. If it requires a tool, output in the format: ACTION: <type> | <json_parameters>. Otherwise, respond normally."
        
        self._conversation_history.append({"role": "user", "content": full_prompt})
        
        try:
            response = self.llm.chat(self._conversation_history)
            self._conversation_history.pop()
        except Exception as e:
            logger.error(f"LLM error: {e}")
            response = "I'm sorry, I encountered an error processing your request."
        
        self._conversation_history.append({"role": "assistant", "content": response})
        
        action, params, clean_response = self._parse_action(response)
        
        if action:
            result = self._execute_action(action, params)
            self._conversation_history.append({"role": "user", "content": f"Action result: {result}"})
            
            final_response = self.llm.chat(self._conversation_history)
            self._conversation_history.append({"role": "assistant", "content": final_response})
            return final_response
        
        return clean_response or response
    
    def _build_context(self) -> str:
        """Build context string for the LLM."""
        context_parts = []
        
        skills_list = self.skills.list_skills()
        if skills_list:
            context_parts.append("Available Skills:")
            for s in skills_list[:20]:
                context_parts.append(f"  - {s['name']}: {s['description'][:100]}")
        
        if self.github:
            user = Config.get("github.username", "")
            if user:
                context_parts.append(f"GitHub User: {user}")
        
        return "\n".join(context_parts)
    
    def _parse_action(self, response: str) -> Tuple[Optional[str], dict, str]:
        """Parse action from LLM response."""
        action_pattern = re.compile(r"ACTION:\s*(\w+)\s*\|\s*(.+)", re.DOTALL)
        match = action_pattern.search(response)
        
        if match:
            action_type = match.group(1).strip()
            json_str = match.group(2).strip()
            
            try:
                params = json.loads(json_str)
            except json.JSONDecodeError:
                params = {}
            
            clean_response = response[:match.start()].strip()
            return action_type, params, clean_response
        
        return None, {}, response
    
    def _execute_action(self, action: str, params: dict) -> str:
        """Execute an action based on type."""
        handler = self._action_handlers.get(action)
        if handler:
            try:
                return handler(**params)
            except Exception as e:
                logger.error(f"Action handler error: {e}")
                return f"Error: {e}"
        return f"Unknown action: {action}"
    
    def _action_github_read(self, owner: str = "", repo: str = "", path: str = "", query: str = "") -> str:
        """Read content from a GitHub repository."""
        if not self.github:
            return "GitHub client not configured."
        
        if path:
            content = self.github.get_file_content(owner, repo, path)
            return content or f"Could not find file {owner}/{repo}/{path}"
        elif query:
            results = self.github.search_code(query)
            files = []
            for item in results[:5]:
                files.append(f"  - {item.get('repository', {}).get('full_name', '')}/{item.get('path', '')}")
            return "\n".join(files) if files else "No results found."
        else:
            readme = self.github.get_repo_readme(owner, repo)
            return readme or f"Could not find repository {owner}/{repo}"
    
    def _action_github_write(self, owner: str = "", repo: str = "", path: str = "", content: str = "", message: str = "") -> str:
        """Write content to a GitHub repository."""
        if not self.github:
            return "GitHub client not configured."
        
        result = self.github.commit_file(owner, repo, path, content, message)
        if result:
            return f"File {path} committed successfully to {owner}/{repo}"
        return f"Failed to commit file to {owner}/{repo}"
    
    def _action_github_pr(self, owner: str = "", repo: str = "", title: str = "", body: str = "", head: str = "", base: str = "main") -> str:
        """Create a pull request."""
        if not self.github:
            return "GitHub client not configured."
        
        result = self.github.create_pull_request(owner, repo, title, body, head, base)
        if result:
            return f"PR created: {result.get('html_url', 'N/A')}"
        return f"Failed to create PR to {owner}/{repo}"
    
    def _action_skill(self, name: str = "", **kwargs) -> str:
        """Execute a skill."""
        return self.skills.execute_skill(name, **kwargs)
    
    def _action_web_search(self, query: str = "", num_results: int = 5) -> str:
        """Search the web."""
        results = self.llm.web_search(query, num_results)
        if results:
            formatted = []
            for r in results:
                formatted.append(f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('snippet', '')}")
            return "\n\n".join(formatted)
        return "No web search results found."
    
    def _action_file_read(self, path: str = "") -> str:
        """Read a file from the local filesystem."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            return f"File not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"
    
    def _action_file_write(self, path: str = "", content: str = "") -> str:
        """Write content to a local file."""
        try:
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File written: {path}"
        except Exception as e:
            return f"Error writing file: {e}"
    
    def _action_shell(self, command: str = "") -> str:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            return output or "(no output)"
        except Exception as e:
            return f"Error executing command: {e}"
    
    def listen_and_respond(self, timeout: float = 10.0) -> str:
        """Listen for voice input and respond."""
        if not self._active:
            return ""
        
        text = self.stt.listen(timeout=timeout)
        if text:
            response = self.process_command(text)
            self.tts.speak(response)
            return response
        return ""
    
    def continuous_listen(self, callback: callable = None):
        """Continuously listen for voice commands."""
        def _listen_loop():
            while self._active and not self._paused:
                text = self.stt.listen(timeout=Config.get("voice.listen_timeout", 10))
                if text:
                    response = self.process_command(text)
                    if callback:
                        callback(text, response)
                    self.tts.speak(response)
                time.sleep(0.5)
        
        self._listen_thread = threading.Thread(target=_listen_loop, daemon=True)
        self._listen_thread.start()
    
    def stop_listening(self):
        """Stop the listening loop."""
        self._active = False
        if hasattr(self, "_listen_thread") and self._listen_thread:
            self._listen_thread.join(timeout=2)
    
    def get_status(self) -> Dict:
        """Get the current status of the agent."""
        return {
            "active": self._active,
            "paused": self._paused,
            "skills_count": len(self.skills.skills),
            "github_connected": self.github is not None,
            "tts_ready": self.tts is not None,
            "stt_backend": self.stt.backend if self.stt else "none",
            "llm_provider": self.llm.provider if self.llm else "none",
            "llm_model": self.llm.model if self.llm else "none",
            "conversation_length": len(self._conversation_history),
            "local_model_enabled": Config.get("local_model.enabled", False)
        }
    
    def clear_history(self):
        """Clear conversation history."""
        self._conversation_history = []
    
    def pause(self):
        """Pause the agent."""
        self._paused = True
    
    def resume(self):
        """Resume the agent."""
        self._paused = False
