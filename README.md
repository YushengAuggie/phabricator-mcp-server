# Phabricator MCP Server

A Model Context Protocol (MCP) server that enables LLMs to interact with Phabricator for task management and code review workflows.

## Features

- **Task Management**: View, comment, and subscribe to Phabricator tasks
- **Code Reviews**: View diffs, read inline comments, approve/reject revisions
- **HTTP/SSE Transport**: Reliable communication with FastMCP (default)
- **Stdio Transport**: Legacy compatibility option

## Quick Start

1. **Get API Token**: Go to your Phabricator Settings → Conduit API Tokens → Generate Token

2. **Setup Environment**:
```bash
git clone https://github.com/YushengAuggie/phabricator-mcp-server.git
cd phabricator-mcp-server
cp .env.example .env
# Edit .env with your token and Phabricator URL
```

3. **Run Server**:
```bash
# Automated setup (recommended)
python3 start.py

# Manual setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/servers/http_server.py
```

The server runs on `http://localhost:8932` by default.

## Configuration

Copy `.env.example` to `.env` and configure:

```env
PHABRICATOR_TOKEN=your-32-character-api-token
PHABRICATOR_URL=https://your-phabricator-instance.com/api/
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black src/ && ruff check src/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.