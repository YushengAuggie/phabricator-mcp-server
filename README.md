# Phabricator MCP Server

A comprehensive Model Context Protocol (MCP) server that enables AI assistants to interact intelligently with Phabricator for advanced task management and code review workflows.

## ✨ Features

### 🔑 **Personal Authentication**
- **Per-User Authentication**: Configure your personal Phabricator API token in your MCP client
- **User Attribution**: Comments and reviews appear under YOUR name instead of a shared service account
- **Flexible Configuration**: Supports both personal tokens and shared environment variables
- **Standard MCP Integration**: Follows MCP ecosystem best practices for authentication

### 🎯 **Core Task Management**
- **Task Operations**: View task details, read comments, add comments, subscribe users to tasks
- **Rich Formatting**: Well-structured output with task metadata, status, priority, and full comment threads

### 🔍 **Advanced Code Review**
- **Differential Management**: View revisions, read comments, approve/reject code changes
- **Intelligent Review Feedback**: Analyze comments with surrounding code context for actionable insights
- **Inline Comments**: Add targeted feedback to specific lines in code reviews
- **Code Context Analysis**: Correlate review comments with actual code changes and locations

### 🚀 **Server Architecture** 
- **HTTP/SSE Transport**: FastMCP-based server for reliable production use (default on port 8932)
- **stdio Transport**: Legacy support for direct MCP client integration
- **Comprehensive API**: 11 specialized tools for complete Phabricator workflow automation

### 🧠 **Smart Review Analysis**
- **Comment-Code Correlation**: Intelligently link review feedback to specific code locations
- **Contextual Code Display**: Show surrounding code lines for better understanding
- **Action Item Generation**: Categorize feedback into actionable to-do items
- **Priority Classification**: Organize comments by Issues → Suggestions → Nits → Other

## 🛠 Available Tools

### **Task Management (3 tools)**
- `get-task` - Get comprehensive task details with comments
- `add-task-comment` - Add comments to tasks
- `subscribe-to-task` - Subscribe users to task notifications

### **Code Review (8 tools)**
- `get-differential` - Get basic differential revision details
- `get-differential-detailed` - Get comprehensive review with code changes
- `get-review-feedback` - : Get intelligent review analysis with code context
- `add-differential-comment` - Add general comments to reviews
- `add-inline-comment` - : Add targeted inline comments to specific code lines
- `accept-differential` - Accept/approve differential revisions
- `request-changes-differential` - Request changes with optional feedback
- `subscribe-to-differential` - Subscribe users to review notifications

## 📋 Prerequisites

- **Python 3.8+**
- **Phabricator instance** with API access
- **API token** from Phabricator (Settings → Conduit API Tokens)

## ⚡ Quick Start

### **Automated Setup (Recommended)**

```bash
# Clone and navigate
git clone https://github.com/YushengAuggie/phabricator-mcp-server.git
cd phabricator-mcp-server

# Configure credentials
echo "PHABRICATOR_TOKEN=your-32-character-api-token" > .env
echo "PHABRICATOR_URL=https://your-phabricator-instance.com/api/" >> .env

# Start server (handles all setup automatically)
python3 start.py --mode http
```

The server starts on `http://localhost:8932` with automatic dependency management.

### **Manual Setup**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with dependencies
pip install -e .

# Start HTTP server
python src/servers/http_server.py

# Or start stdio server
python src/servers/stdio_server.py
```

## ⚙️ Configuration

### **Authentication Configuration**

The server supports **hybrid authentication** with two modes that work seamlessly together:

1. **Personal API Token (Recommended)**: Pass your personal token through MCP client configuration for user attribution
2. **Environment Variable Fallback**: Use a shared service account token via environment variables

**🔑 Getting Your API Token:**
1. Go to your Phabricator instance → Settings → API Tokens
2. Create a new token with appropriate permissions
3. Copy the 32-character token for use in configuration

**🌐 Finding Your Phabricator URL:**
Your Phabricator API URL should end with `/api/` and typically looks like:
- `https://phabricator.example.com/api/`
- `https://phab.yourcompany.com/api/`
- `https://your-domain.phabricator.com/api/`

If unsure, check your Phabricator instance's main page - the URL is usually `[your-base-url]/api/`

### **🚀 MCP Client Configuration**

#### **HTTP/SSE Transport (Recommended)**

The server automatically detects your environment configuration:

**Claude Code CLI (Easiest):**
```bash
claude mcp add --transport sse phabricator http://localhost:8932/sse \
  --env "PHABRICATOR_TOKEN=api-xxxxxxx" \
  --env "PHABRICATOR_URL=https://example.com/api/"
```

> Replace `api-xxxxxxx` with your actual API token and `https://example.com/api/` with your Phabricator instance URL

**Manual Configuration:**
```json
{
  "mcpServers": {
    "phabricator": {
      "url": "http://localhost:8932/sse",
      "env": {
        "PHABRICATOR_TOKEN": "api-xxxxxxx",
        "PHABRICATOR_URL": "https://example.com/api/"
      }
    }
  }
}
```

#### **stdio Transport**

For Claude Desktop and direct MCP integration:

```json
{
  "mcpServers": {
    "phabricator": {
      "command": "python",
      "args": ["path/to/phabricator-mcp-server/start.py"],
      "cwd": "path/to/phabricator-mcp-server",
      "env": {
        "PHABRICATOR_TOKEN": "api-xxxxxxx",
        "PHABRICATOR_URL": "https://example.com/api/"
      }
    }
  }
}
```

#### **Multiple Authentication Options**

The server supports multiple ways to authenticate:

1. **Personal Token in Tools**: Some tools accept an `api_token` parameter
2. **Environment Variables**: Set `PHABRICATOR_TOKEN` in MCP client config
3. **Fallback Token**: Create `.env` file in server directory

**Priority Order**: Personal token → MCP environment → Server `.env` file

#### **Server Environment Variables (Fallback)**

Create `.env` file in project root for fallback authentication:

```env
# Fallback: Shared service account token  
PHABRICATOR_TOKEN=your-shared-token-here

# Optional: Custom Phabricator URL (auto-detected from token by default)
# PHABRICATOR_URL=https://your-phabricator-instance.com/api/

# Optional: Custom server port (default: 8932)
# MCP_SERVER_PORT=8932
```

### **🔧 Advanced Configuration**

#### **User Attribution**
- **Personal tokens**: Comments appear under YOUR name
- **Shared tokens**: Comments appear under the service account name
- **Mixed usage**: Different tools can use different tokens

#### **Token Security**
- Tokens are passed securely through MCP protocol
- No tokens stored on disk (except optional `.env` fallback)
- Each client can use their own personal token

#### **Troubleshooting Authentication**

If you see authentication errors:

1. **Check token validity**: Test your token directly with Phabricator API
2. **Verify configuration**: Ensure `PHABRICATOR_TOKEN` is set correctly
3. **Check environment**: Run server with debugging to see environment variables
4. **Use personal token**: Pass `api_token` parameter directly to tools

**Debugging Commands:**
```bash
# Check if server can start with your token
PHABRICATOR_TOKEN=your-token python start.py --mode http

# Test token manually
curl -d "api.token=your-token" https://your-phabricator-instance.com/api/user.whoami
```

## 💻 Usage

### **With Claude Desktop**

Add to Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "phabricator": {
      "command": "python",
      "args": ["path/to/phabricator-mcp-server/start.py", "--mode", "stdio"],
      "cwd": "path/to/phabricator-mcp-server"
    }
  }
}
```

### **With HTTP/SSE Transport**

```json
{
  "mcpServers": {
    "phabricator": {
      "url": "http://localhost:8932/sse"
    }
  }
}
```

### **Programmatic Usage**

```python
from src.core.client import PhabricatorClient

# Initialize client
client = PhabricatorClient(
    token="your-32-char-api-token",
    host="https://your-instance.com/api/"
)

# Get enhanced review feedback with code context
feedback = await client.get_review_feedback_with_code_context("12345", context_lines=7)

# Add inline comment to specific line
await client.add_inline_comment("12345", "src/file.py", 42, "Consider using a more descriptive variable name")

# Get task with full context
task = await client.get_task("6789")
comments = await client.get_task_comments("6789")
```

### **Example: AI-Powered Code Review**

```python
# Get intelligent review feedback
feedback_data = await client.get_review_feedback_with_code_context("D123", context_lines=5)

# The feedback includes:
# - Comments correlated with specific code locations
# - Surrounding code context for each comment
# - Action items categorized by priority
# - File-by-file breakdown of changes
```

## 🧪 Development & Testing

### **Install Development Dependencies**

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"
```

### **Run Tests**

```bash
# Run all tests with our test runner
python run_tests.py

# Run specific test suites
python -m pytest src/tests/test_tool_completeness.py -v
python -m pytest src/tests/test_tool_integration.py -v

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

### **Code Quality**

```bash
# Format code
black src/
ruff check src/ --fix

# Type checking
mypy src/

# Run all quality checks
black src/ && ruff check src/ && mypy src/ && python run_tests.py
```

### **Testing Features**
- **Tool Completeness**: Validates all 11 tools are properly configured
- **Integration Testing**: Tests all tools with realistic mock data
- **Error Handling**: Validates graceful failure modes
- **Argument Validation**: Ensures correct required/optional parameters
- **Mock Phabricator**: No API calls needed for testing

## 🎯 Advanced Features

### **Intelligent Review Feedback Analysis**

The `get-review-feedback` tool provides advanced analysis:

```python
# Returns structured feedback with:
{
    "revision": {...},              # Revision metadata
    "review_feedback": [            # Enhanced comment analysis
        {
            "comment": "Fix this issue",
            "author": "reviewer-phid",
            "type": "inline",
            "code_context": {
                "file": "src/example.py",
                "target_line": 42,
                "hunk_info": "@@ -40,7 +40,7 @@",
                "lines": [           # Surrounding code context
                    {"line_number": 40, "content": "def example():", "is_target": False},
                    {"line_number": 41, "content": "    # TODO: fix this", "is_target": False},
                    {"line_number": 42, "content": "    return broken_code", "is_target": True},
                    {"line_number": 43, "content": "    # end function", "is_target": False},
                ]
            },
            "primary_file": "src/example.py",
            "primary_line": 42
        }
    ],
    "summary": "Analysis summary with actionable insights",
    "total_comments": 5,
    "comments_with_context": 3
}
```

### **Smart Comment-Code Correlation**

- **Keyword Extraction**: Identifies variable names, function names in comments
- **Code Location Mapping**: Links comments to specific files and line numbers  
- **Context Enrichment**: Shows surrounding code for better understanding
- **Priority Classification**: Organizes feedback by importance

## 🤝 Contributing

We welcome contributions! Here's how to get started:

```bash
# Fork and clone the repository
git clone https://github.com/your-username/phabricator-mcp-server.git
cd phabricator-mcp-server

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
python run_tests.py

# Commit and push
git commit -m 'feat: add amazing feature'
git push origin feature/amazing-feature

# Open a Pull Request
```

### **Development Guidelines**
- Follow existing code style (black + ruff)
- Add tests for new features
- Update documentation as needed
- Ensure all quality checks pass

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: https://github.com/YushengAuggie/phabricator-mcp-server
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **FastMCP**: https://github.com/jlowin/fastmcp
- **Phabricator API**: https://secure.phabricator.com/book/phabricator/article/conduit/