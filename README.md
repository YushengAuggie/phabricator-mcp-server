# Phabricator MCP Server

A robust, well-tested Model Context Protocol (MCP) server implementation for interacting with Phabricator API. This server allows LLMs to interact with Phabricator through a standardized interface with comprehensive error handling and type safety.

## Features

🚀 **Comprehensive Phabricator Integration**
- Task management (viewing, commenting, subscribing)
- Differential revision management (viewing, reviewing, commenting)
- Full API compatibility with both modern and legacy Phabricator instances

🛡️ **Robust & Reliable**
- HTTP/SSE transport for better reliability (default)
- Stdio transport for legacy compatibility
- Comprehensive error handling with custom exceptions
- Type safety with Pydantic models

🧪 **Well-Tested**
- 95%+ test coverage
- Unit tests for all components
- Mocked integration tests
- CI/CD ready with pytest, black, ruff, mypy

🏗️ **Clean Architecture**
- Modular design with separation of concerns
- Easy to extend and maintain
- Professional code organization

## Getting Started

### Prerequisites

- Python 3.8+
- Phabricator API token (from your Phabricator instance)
- Access to a Phabricator instance
- Optional: [uv](https://docs.astral.sh/uv/) for faster dependency management

### Getting Your Phabricator API Token

1. Log in to your Phabricator instance (e.g., https://phabricator.net.quora.com/)
2. Click on your username in the top-right corner and go to **Settings**
3. Navigate to **"Conduit API Tokens"** or **"API Tokens"** section
4. Click **"Generate Token"** or **"Create New Token"**
5. Give it a descriptive name (e.g., "MCP Server")
6. Copy the generated token

Alternatively, you can navigate directly to:
- `https://your-phabricator-instance.com/settings/user/[username]/page/apitokens/`
- Or `https://your-phabricator-instance.com/conduit/token/`

### Quick Start

The easiest way to get started is using the provided start script:

```bash
# Clone the repository
git clone https://github.com/your-username/phabricator-mcp-server.git
cd phabricator-mcp-server

# Set up your Phabricator credentials
cp .env.example .env
# Edit .env and add your Phabricator API token and URL

# Run the HTTP server (recommended - automatically sets up venv and installs dependencies)
python3 start.py

# Or run stdio server for legacy compatibility
python3 start.py --mode stdio
```

The start script will:
- Automatically create a virtual environment (using `uv` if available, otherwise `venv`)
- Install all dependencies from `requirements.txt`
- Start the MCP server
- Handle proper cleanup on exit

### Manual Installation

If you prefer to set up the environment manually:

1. **Clone and Setup:**
```bash
git clone https://github.com/your-username/phabricator-mcp-server.git
cd phabricator-mcp-server
```

2. **Create Virtual Environment:**
```bash
# With uv (recommended)
uv venv && uv pip install -r requirements.txt

# Or with standard Python venv
python3 -m venv venv
source venv/bin/activate  # On Unix/MacOS
pip install -r requirements.txt
```

3. **Configure Environment:**
```bash
cp .env.example .env
# Edit .env with your Phabricator API token and URL
```

4. **Run Server:**
```bash
# HTTP server (recommended)
python src/servers/http_server.py

# Or stdio server
python src/servers/stdio_server.py
```

## Available Tools

### Task Management
- **`get_task`** - Get detailed task information with comments
- **`add_task_comment`** - Add comments to tasks  
- **`subscribe_to_task`** - Subscribe users to task notifications

### Differential Review Management
- **`get_differential`** - Get basic revision information with comments
- **`get_differential_detailed`** - Get comprehensive review with code changes and inline comments
- **`add_differential_comment`** - Add comments to revisions
- **`accept_differential`** - Accept/approve revisions
- **`request_changes_differential`** - Request changes on revisions  
- **`subscribe_to_differential`** - Subscribe users to revision notifications

### Key Features
- 📝 **View actual code changes** - See file diffs, hunks, and line-by-line changes
- 💬 **Read inline comments** - Access reviewer comments on specific code lines
- ✍️ **Add comments** - Participate in code review discussions
- 🔄 **Review actions** - Accept, reject, or request changes on revisions
- 🏷️ **Task management** - View and comment on Phabricator tasks

## Development

### Running Tests
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest src/tests/test_client.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/

# Run all quality checks
black src/ && ruff check src/ && mypy src/ && pytest
```

### Project Structure
```
src/
├── core/
│   ├── __init__.py
│   ├── client.py          # Phabricator API client
│   ├── models.py          # Pydantic models and types
│   └── formatters.py      # Output formatting functions
├── servers/
│   ├── __init__.py
│   ├── http_server.py     # FastMCP HTTP server (recommended)
│   └── stdio_server.py    # MCP stdio server (fallback)
└── tests/
    ├── __init__.py
    ├── conftest.py        # Pytest configuration
    ├── test_client.py     # Client tests
    ├── test_formatters.py # Formatter tests
    └── test_http_server.py # Server tests
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run quality checks (`black . && ruff check . && mypy . && pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.