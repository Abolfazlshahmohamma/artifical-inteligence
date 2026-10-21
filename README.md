# WakeUp Agent

**The Unstoppable AI Agent for Windows**

A powerful, modular AI agent that activates by typing "its time to wake up" anywhere, listens to voice commands, and executes tasks with full GitHub integration, skills discovery, and multi-model AI support.

## Features

- **Voice Activation**: Type `its time to wake up` in any cmd window to activate
- **Voice-to-Text**: Offline speech recognition via Windows SAPI
- **Text-to-Speech**: Offline voice output via Windows SAPI
- **Multi-Model AI**: Supports OpenRouter, OpenAI, Anthropic, DeepSeek, Ollama
- **GitHub Integration**: Read repos, create issues, PRs, commit files
- **Skills Engine**: Discovers and uses skills from GitHub repositories
- **Web Access**: Web search, HTTP API calls, web browsing capabilities
- **Professional GUI**: Modern dark-themed Tkinter interface
- **Offline Mode**: Works without internet using local models (Ollama)
- **Keyboard Hook**: Global keyboard listener for instant activation

## Quick Start

### Installation

```powershell
cd C:\wake_up_agent
python install.py --setup
```

This will:
1. Set up PATH environment variable
2. Create startup script for auto-launch
3. Create desktop shortcut
4. Prompt for API keys (interactive)

### Usage

1. Start the agent (auto-starts if installed, or run manually):
   ```
   python C:\wake_up_agent\main.py
   ```

2. Type `its time to wake up` in any cmd window to activate

3. Or use the shortcut:
   ```
   wake
   ```

4. The GUI will appear and the agent will say "I'm awake. How can I help you?"

5. Speak your command or type it in the GUI input box

## Configuration

Edit `config.json` to configure:

```json
{
    "activation_phrase": "its time to wake up",
    "llm": {
        "provider": "openrouter",
        "api_key": "YOUR_API_KEY_HERE",
        "model": "google/gemini-2.5-flash"
    },
    "github": {
        "token": "YOUR_GITHUB_TOKEN",
        "username": "your_username"
    },
    "voice": {
        "wake_word": "hey agent",
        "listen_timeout": 10,
        "language": "en-US"
    }
}
```

### Supported LLM Providers

| Provider | Setup |
|----------|-------|
| OpenRouter | `provider: "openrouter"`, get key from https://openrouter.ai/keys |
| OpenAI | `provider: "openai"`, get key from https://platform.openai.com |
| Anthropic | `provider: "anthropic"`, get key from https://console.anthropic.com |
| DeepSeek | `provider: "deepseek"`, get key from https://platform.deepseek.com |
| Ollama (local) | `provider: "ollama"`, run `ollama serve` locally |

## Architecture

```
wake_up_agent/
├── main.py               # Entry point - background daemon
├── config.py             # Configuration manager
├── agent.py              # Core agent orchestrator
├── install.py            # Installation script
├── run.py                # Quick test/launch script
├── config.json           # Configuration file
├── cli/
│   ├── wake_listener.py  # Global keyboard hook listener
│   └── activate.py       # CLI activation tool
├── voice/
│   ├── stt.py            # Speech-to-text (multiple backends)
│   └── tts.py            # Text-to-speech (Windows SAPI)
├── llm/
│   └── client.py         # Multi-provider LLM client
├── github_client.py      # GitHub API client
├── skills/
│   └── engine.py         # Skills discovery & execution engine
├── gui/
│   └── app.py            # Tkinter GUI application
├── ipc/
│   └── server.py         # Windows named pipe IPC
└── utils/
    └── logger.py         # Logging utility
```

## Agent Capabilities

### Voice Commands
- "What's the weather today?"
- "Search the web for AI news"
- "Read the README of Kilo-Org/kilocode"
- "Create a file called test.txt with hello world"
- "List my GitHub repositories"
- "Install the skill from github.com/Kilo-Org/kilocode"

### GitHub Actions
- Read repository files and directories
- Search code across GitHub
- Create issues and pull requests
- Commit files to repositories
- List branches, contributors, languages

### Skills Engine
- Auto-discovers agent skills from GitHub repos
- Loads local skills from `skills_repo/` directory
- Supports Python, shell, and LLM-based skills
- Skills can be executed by name or by natural language query

## Development

### Testing
```bash
# Full test (agent + GUI)
python run.py --test

# GUI only test
python run.py --gui-test

# Voice test (TTS + STT)
python run.py --voice-test
```

### Creating a Custom Skill
1. Create a directory in `skills_repo/`
2. Add `skill.json`:
   ```json
   {
       "name": "my_skill",
       "description": "What this skill does",
       "type": "python",
       "entry_point": "run.py",
       "parameters": [{"name": "query", "type": "string"}],
       "tags": ["example"]
   }
   ```
3. Add your Python script

## System Requirements

- Windows 10/11
- Python 3.12+
- Microphone (for voice input)
- Speakers (for voice output)
- Internet (for AI models, or use Ollama for offline)

## License

MIT
