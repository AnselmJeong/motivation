# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Motivational Interviewing Multi-Agent System built with Google Agent Development Kit (ADK) that simulates realistic MI therapy sessions through three specialized agents:

- **TherapistAgent**: MI expert conducting the interview
- **ClientAgent**: Patient role simulation with realistic responses 
- **SupervisorAgent**: Provides real-time feedback to therapist

The system uses a sequential workflow where agents interact in turns (Therapist → Client → Supervisor → ConversationManager) within a loop for complete sessions.

## Development Commands

### Environment Setup
```bash
# Install dependencies (preferred method)
uv sync

# Alternative installation
pip install -e .
```

### Running the System
```bash
# Run example scenarios
python hello.py

# Direct module execution  
python -m generator_critic.agent

# Custom session execution (modify parameters in script)
python generator_critic/agent.py
```

### Testing
The project currently uses example scenarios in `hello.py` for testing. No automated test framework is configured.

## Architecture

### Core Components
- **MotivationalInterviewingSystem**: Main orchestrator managing the entire session flow
- **Agent Classes**: `TherapistAgent`, `ClientAgent`, `SupervisorAgent` inherit from Google ADK's `LlmAgent`
- **ConversationManager**: Controls session termination and flow management
- **Session Recording**: Automatic markdown generation in `output/` directory

### Multi-Agent Workflow
The system implements a sequential agent pattern wrapped in a loop:
1. `SequentialAgent` coordinates turn-based execution
2. `LoopAgent` manages session repetition (max 100 interactions)
3. Shared session state enables agent communication
4. Natural termination detection through keyword analysis

### Session State Management
All agents access shared session state containing:
- `client_problem`: Detailed problem description
- `session_goal`: Session objectives
- `reference_material`: MI techniques and principles
- `conversation_history`: Complete dialogue record
- `current_turn`: Turn counter for flow control

### Google ADK Integration
- Uses Gemini-2.5-flash model for all agents
- Implements `InMemorySessionService` for session management
- Includes mock classes for development without ADK installation
- Automatic `.env` file detection for API keys

## Key Implementation Details

### Agent Instructions
Each agent has specialized instructions:
- Therapist follows MI principles (OARS technique)
- Client exhibits realistic ambivalence and resistance
- Supervisor provides structured feedback (strengths, improvements, suggestions, direction)

### Termination Logic
Sessions end when:
- Maximum interactions reached (configurable, default 100)
- Natural ending phrases detected ("감사합니다", "세션 종료", etc.)
- Minimum 3 turns enforced to prevent premature termination

### Output Format
Sessions generate structured markdown files in `output/` with:
- Session metadata (timestamp, problem, goals)
- Turn-by-turn conversation records
- Speaker identification with emojis (🩺 Therapist, 😊 Client, 👨‍🏫 Supervisor)

## Usage Patterns

### Synchronous Execution
```python
from generator_critic.agent import run_mi_session_sync

output_file = run_mi_session_sync(
    client_problem="detailed problem description",
    session_goal="specific objectives", 
    reference_material="MI techniques",
    max_interactions=10
)
```

### Asynchronous Execution  
```python
from generator_critic.agent import create_mi_session

output_file = await create_mi_session(
    client_problem="...",
    session_goal="...", 
    reference_material="...",
    max_interactions=20
)
```

### System Class Usage
```python
from generator_critic.agent import MotivationalInterviewingSystem

mi_system = MotivationalInterviewingSystem(max_interactions=50)
output_file = await mi_system.run_session(...)
```

## File Structure
- `generator_critic/agent.py`: Main system implementation
- `hello.py`: Example scenarios and test cases
- `output/`: Generated session records (auto-created)
- `pyproject.toml`: Dependencies (requires Python 3.13+, Google ADK 1.5.0+)