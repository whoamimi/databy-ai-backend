# DataBy AI - Autonomous Data Agent

![PyPI version](https://img.shields.io/pypi/v/databy.svg)
[![Documentation Status](https://readthedocs.org/projects/databy/badge/?version=latest)](https://databy.readthedocs.io/en/latest/?version=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Autonomous AI agent for complete data lifecycle management** - From raw data ingestion to actionable insights, fully automated.

## Table of Contents

- [DataBy AI - Autonomous Data Agent](#databy-ai---autonomous-data-agent)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Architecture](#architecture)
  - [Quick Start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Running the Server](#running-the-server)
  - [Usage](#usage)
    - [API Endpoints](#api-endpoints)
    - [WebSocket Interface](#websocket-interface)
    - [CLI Commands](#cli-commands)
  - [Development](#development)
    - [Setup Development Environment](#setup-development-environment)
    - [Running Tests](#running-tests)
    - [Code Quality](#code-quality)
  - [Agent System](#agent-system)
    - [Core Components](#core-components)
    - [Pipeline Stages](#pipeline-stages)
    - [Real-time Monitoring](#real-time-monitoring)
  - [API Reference](#api-reference)
  - [License](#license)

## Overview

DataBy AI is an intelligent, autonomous agent system designed to handle the complete data analysis lifecycle without human intervention. Built with FastAPI and powered by modern AI models, it provides end-to-end data processing capabilities through both REST API and real-time WebSocket interfaces.

The system automatically:
- 🔍 **Explores** and analyzes data structure and quality
- 🧹 **Cleans** and preprocesses datasets intelligently
- 📊 **Analyzes** patterns and generates insights
- 🤖 **Learns** from data to improve future processing
- 📋 **Reports** findings in structured formats
- ⚡ **Streams** real-time progress updates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DataBy AI Architecture                   │
├─────────────────────────────────────────────────────────────┤
│  Frontend / Clients                                         │
│  ├─ Web Interface (WebSocket)                              │
│  ├─ CLI Tools                                              │
│  └─ API Clients (REST)                                     │
├─────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI)                                       │
│  ├─ REST Endpoints (/api/*)                               │
│  ├─ WebSocket Handler (/agent/ws)                         │
│  ├─ Documentation (/docs)                                 │
│  └─ Health & Status (/health, /agent/status)             │
├─────────────────────────────────────────────────────────────┤
│  Agent Core                                                 │
│  ├─ Cognitive Engine (AI Decision Making)                 │
│  ├─ Pipeline Manager (Workflow Orchestration)             │
│  ├─ Heartbeat System (Monitoring & Status)                │
│  └─ Memory System (Knowledge Storage)                     │
├─────────────────────────────────────────────────────────────┤
│  Processing Pipelines                                       │
│  ├─ Data Explorer (Structure Analysis)                    │
│  ├─ Data Cleaner (Quality & Preprocessing)                │
│  ├─ Statistical Methods (Analysis & Insights)             │
│  └─ Missing Data Handler (Imputation Strategies)          │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                             │
│  ├─ Configuration Management                               │
│  ├─ Logging & Monitoring                                  │
│  └─ Settings & Environment                                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)
- **Git** (for development)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd databy-ai/backend
   ```

2. **Create virtual environment & setup env variables**:
   Update all env variables in `.env.example` with your info.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Set up environment**:
   ```bash
   cp .env.example .env  # Configure as needed
   ```

### Running the Server

**Development Mode**:
```bash
python -m app serve --reload
```

**Production Mode**:
```bash
python -m app serve --host 0.0.0.0 --port 8000
```

**Using CLI**:
```bash
databy serve --port 8000
```

The server will start on `http://localhost:8000` with:
- 📚 **API Documentation**: `http://localhost:8000/api/docs`
- 🔌 **WebSocket Endpoint**: `ws://localhost:8000/agent/ws`
- ❤️ **Health Check**: `http://localhost:8000/health`

## Usage

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API metadata and version info |
| `/health` | GET | Service health status |
| `/agent/status` | GET | Current agent status |
| `/agent/ws` | WebSocket | Real-time agent communication |

### WebSocket Interface

Connect to `ws://localhost:8000/agent/ws` for real-time communication:

```javascript
const ws = new WebSocket('ws://localhost:8000/agent/ws');

// Subscribe to agent updates
ws.send(JSON.stringify({
    "type": "subscribe"
}));

// Get current status
ws.send(JSON.stringify({
    "type": "getStatus"
}));

// Request data analysis
ws.send(JSON.stringify({
    "type": "cleanReport"
}));
```

### CLI Commands

```bash
# Start the server
databy serve

# Show help
databy --help

# Run data processing
databy process --input data.csv

# Check agent status
databy status
```

## Development

### Setup Development Environment

1. **Install development dependencies**:
   ```bash
   pip install -e ".[dev,test]"
   ```

2. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Run development server**:
   ```bash
   python -m app serve --reload
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_main.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Check typing
mypy app/

# Lint code
ruff check app/
```

## Agent System

### Core Components

- **Cognitive Engine**: AI-powered decision making and strategy selection
- **Pipeline Manager**: Orchestrates data processing workflows
- **Heartbeat System**: Real-time status monitoring and health checks
- **Memory System**: Stores knowledge and learns from past processing

### Pipeline Stages

1. **Data Exploration**: Structure analysis, type detection, basic statistics
2. **Missing Data Analysis**: MCAR/MAR/MNAR classification and handling strategies
3. **Data Cleaning**: Quality assessment, outlier detection, preprocessing
4. **Statistical Analysis**: Descriptive statistics, pattern recognition, insights
5. **Report Generation**: Structured findings and recommendations

### Real-time Monitoring

The system provides real-time updates through WebSocket connections:
- **Status Updates**: Current processing stage and progress
- **Heartbeat Messages**: System health and performance metrics
- **Error Notifications**: Detailed error context and recovery suggestions
- **Completion Reports**: Final results and insights

## API Reference

Full API documentation is available at `/api/docs` when the server is running, or visit our [online documentation](https://databy.readthedocs.io).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

This package was created with [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
