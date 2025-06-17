# Phabricator MCP Server

A Model Context Protocol (MCP) server that enables LLMs to interact with Phabricator for task management and code review workflows.

## Features

### Core Capabilities
- **Task Management**: View tasks, read comments, add comments, subscribe to tasks
- **Code Reviews**: View differential revisions, read inline comments, approve/reject revisions
- **Multiple Transports**: HTTP/SSE via FastMCP (default) or stdio for legacy support

### Enhanced Features (Experimental)
- **Code Context**: View inline comments with surrounding code context
- **Enhanced Formatting**: Better organization of comments by type and file

## Installation

### Prerequisites
- Python 3.8+
- Phabricator instance with API access
- API token from Phabricator (Settings → Conduit API Tokens)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/YushengAuggie/phabricator-mcp-server.git
cd phabricator-mcp-server

# Setup environment
cp .env.example .env
# Edit .env with your Phabricator token and URL

# Run with automated setup (recommended)
python3 start.py

# Or manual setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/servers/http_server.py
```

The server runs on `http://localhost:8932` by default.

## Configuration

Create a `.env` file from `.env.example`:

```env
PHABRICATOR_TOKEN=your-32-character-api-token
PHABRICATOR_URL=https://your-phabricator-instance.com/api/
```

## Project Structure

```
phabricator-mcp-server/
├── src/
│   ├── core/               # Core functionality
│   │   ├── client.py       # Basic Phabricator API client
│   │   ├── enhanced_client.py  # Enhanced client with code context
│   │   ├── models.py       # Data models
│   │   ├── formatters.py   # Basic output formatting
│   │   └── enhanced_formatters.py  # Enhanced formatting
│   ├── servers/            # Server implementations
│   │   ├── http_server.py  # FastMCP HTTP/SSE server
│   │   └── stdio_server.py # Legacy stdio server
│   └── tests/              # Test suite
├── examples/               # Example usage scripts
├── scripts/                # Utility and debug scripts
├── start.py               # Main entry point
└── requirements.txt       # Dependencies
```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "phabricator": {
      "command": "python",
      "args": ["path/to/start.py"]
    }
  }
}
```

### Programmatic Usage

```python
from src.core.client import PhabricatorClient

# Initialize client
client = PhabricatorClient(
    token="your-api-token",
    url="https://your-instance.com/api/"
)

# Get task details
task = await client.get_task("T123")

# View differential revision
revision = await client.get_differential_revision("D456")
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black src/
ruff check src/

# Type checking
pyright src/
```

### Testing
- Unit tests: `pytest src/tests/`
- Specific test: `pytest src/tests/test_file.py::test_function`
- Coverage: `pytest --cov=src`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.