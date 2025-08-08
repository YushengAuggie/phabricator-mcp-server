#!/usr/bin/env python3
"""
Phabricator MCP Server Startup Script

This script provides a convenient way to start the Phabricator MCP server
from the root directory. It automatically handles virtual environment setup
and dependency installation using either uv or pip.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command with proper error handling."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if not capture_output:
            print(f"Command failed: {cmd}")
            print(f"Error: {e}")
        return None


def has_uv():
    """Check if uv is available."""
    return shutil.which("uv") is not None


def has_venv():
    """Check if virtual environment exists."""
    venv_path = Path("venv")
    return venv_path.exists() and (venv_path / "bin" / "python").exists()


def create_venv():
    """Create virtual environment using uv or venv."""
    print("Creating virtual environment...")

    if has_uv():
        print("Using uv to create virtual environment...")
        result = run_command("uv venv")
        if result is None:
            print("Failed to create virtual environment with uv")
            return False
    else:
        print("Using python venv to create virtual environment...")
        result = run_command("python3 -m venv venv")
        if result is None:
            print("Failed to create virtual environment with venv")
            return False

    return True


def install_dependencies():
    """Install dependencies using uv or pip."""
    print("Installing dependencies...")

    if has_uv():
        print("Using uv to install dependencies...")
        result = run_command("uv pip install -e .")
        if result is None:
            print("Failed to install dependencies with uv")
            return False
    else:
        # Activate venv and install with pip
        if sys.platform == "win32":
            pip_cmd = r"venv\Scripts\pip"
        else:
            pip_cmd = "venv/bin/pip"

        result = run_command(f"{pip_cmd} install -e .")
        if result is None:
            print("Failed to install dependencies with pip")
            return False

    return True


def get_python_executable():
    """Get the appropriate Python executable."""
    if has_uv():
        # uv creates venv in same structure as regular venv
        if sys.platform == "win32":
            return r"venv\Scripts\python"
        else:
            return "venv/bin/python"
    else:
        # Use venv python
        if sys.platform == "win32":
            return r"venv\Scripts\python"
        else:
            return "venv/bin/python"


def check_env_file():
    """Check if .env file exists and has PHABRICATOR_TOKEN."""
    env_file = Path(".env")
    if not env_file.exists():
        print("Warning: .env file not found!")
        print("Create a .env file with your PHABRICATOR_TOKEN:")
        print("echo 'PHABRICATOR_TOKEN=your-token-here' > .env")
        return False

    try:
        env_content = env_file.read_text()
        if "PHABRICATOR_TOKEN" not in env_content:
            print("Warning: PHABRICATOR_TOKEN not found in .env file!")
            return False
    except Exception as e:
        print(f"Error reading .env file: {e}")
        return False

    return True


def setup_environment():
    """Set up the development environment."""
    # Check if pyproject.toml exists
    if not Path("pyproject.toml").exists():
        print("Error: pyproject.toml not found!")
        return False

    # Create virtual environment if it doesn't exist
    if not has_venv():
        if not create_venv():
            return False

    # Install dependencies
    if not install_dependencies():
        return False

    return True


def start_server(mode="stdio"):
    """Start the MCP server in either stdio or http mode."""
    # Add the src directory to the Python path
    src_dir = Path(__file__).parent / "src"

    python_exe = get_python_executable()

    # Set PYTHONPATH to include src directory
    env = os.environ.copy()
    # Clear PYTHONPATH to avoid conflicts with system paths
    env["PYTHONPATH"] = str(src_dir)
    # Also set PYTHONNOUSERSITE to ignore user site-packages
    env["PYTHONNOUSERSITE"] = "1"

    if mode == "http":
        print("🚀 Starting Phabricator MCP HTTP Server")
        print("📡 Server will be available at: http://localhost:8932")
        print("🔗 MCP Endpoint: http://localhost:8932/sse")
        print()
        print("📋 Setup Instructions:")
        print()
        print("🚀 Option 1: Claude Code CLI (Recommended)")
        print("claude mcp add --transport sse phabricator http://localhost:8932/sse \\")
        print("  --env \"PHABRICATOR_TOKEN=api-xxxxxxx\" \\")
        print("  --env \"PHABRICATOR_URL=https://example.com/api/\"")
        print()
        print("🔧 Option 2: Manual Configuration")
        print("Add this to your MCP configuration file:")
        print('{')
        print('  "mcpServers": {')
        print('    "phabricator": {')
        print('      "url": "http://localhost:8932/sse",')
        print('      "env": {')
        print('        "PHABRICATOR_TOKEN": "api-xxxxxxx",')
        print('        "PHABRICATOR_URL": "https://example.com/api/"')
        print('      }')
        print('    }')
        print('  }')
        print('}')
        print()
        print("🔑 Authentication:")
        print("• Personal API Token: Configure your individual Phabricator API token")
        print("• User Attribution: Comments and reviews will appear under YOUR name")
        print("• Hybrid Support: Falls back to environment variables if no personal token")
        print("• Secure: Token is passed through MCP client configuration")
        print("• Replace 'api-xxxxxxx' with your actual API token")
        print("• Replace 'https://example.com/api/' with your actual Phabricator URL")
        print()
        print("💡 Getting Your API Token:")
        print("   1. Go to your Phabricator instance → Settings → API Tokens")
        print("   2. Create a new token with appropriate permissions")
        print("   3. Use this token in your MCP client configuration")
        print()
        print("🌐 Finding Your Phabricator URL:")
        print("   Your API URL should end with /api/ (e.g., https://phab.company.com/api/)")
        print("   Set PHABRICATOR_URL in your MCP client environment configuration")
        print()
        print("📝 Usage Examples:")
        print('  get_task(task_id="12345")')
        print('  add_task_comment(task_id="12345", comment="Fixed!")')
        print('  get_differential_detailed(revision_id="67890")')
        print('  add_differential_comment(revision_id="67890", comment="LGTM!")')
        print()
        print("🛠️ Available tools:")
        print("• get_task - Get task details")
        print("• add_task_comment - Add comment to task")
        print("• subscribe_to_task - Subscribe users to task")
        print("• get_differential - Get differential revision details")
        print("• get_differential_detailed - Get comprehensive review with code changes")
        print("• get_review_feedback - Get review feedback with intelligent code context")
        print("• add_differential_comment - Add comment to differential")
        print("• add_inline_comment - Add inline comment to specific line")
        print("• accept_differential - Accept differential revision")
        print("• request_changes_differential - Request changes on differential")
        print("• subscribe_to_differential - Subscribe users to differential")
        print()
        print("Press Ctrl+C to stop the server")

        try:
            # Run the HTTP server with --quiet flag to prevent duplicate output
            subprocess.run(
                [python_exe, str(src_dir / "servers" / "http_server.py"), "--quiet"],
                env=env,
                check=True,
            )
        except KeyboardInterrupt:
            print("\nHTTP Server stopped by user")
        except subprocess.CalledProcessError as e:
            print(f"Error starting HTTP server: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    else:  # stdio mode
        print("Starting Phabricator MCP Server (stdio mode)...")
        print()
        print("Server Configuration:")
        print("=" * 40)
        print("Server URL: stdio://phabricator-mcp-server")
        print("Port: stdio (standard input/output)")
        print()
        print("Add this to your MCP client configuration:")
        print('{')
        print('  "mcpServers": {')
        print('    "phabricator": {')
        print('      "command": "python",')
        print(f'      "args": ["{os.path.abspath("start.py")}"],')
        print('      "cwd": "' + os.getcwd() + '",')
        print('      "env": {')
        print('        "PHABRICATOR_TOKEN": "api-xxxxxxx",')
        print('        "PHABRICATOR_URL": "https://example.com/api/"')
        print('      }')
        print('    }')
        print('  }')
        print('}')
        print()
        print("🔑 Authentication:")
        print("• Configure your personal Phabricator API token in the MCP client configuration")
        print("• Set PHABRICATOR_URL to point to your Phabricator instance's API endpoint")
        print("• Token is set once when the server starts")
        print("• Comments and reviews will appear under YOUR name")
        print()
        print("📝 Usage Examples:")
        print('  mcp__phabricator__get_task(task_id="12345")')
        print('  mcp__phabricator__add_task_comment(task_id="12345", comment="Fixed!")')
        print('  mcp__phabricator__get_differential_detailed(revision_id="67890")')
        print('  mcp__phabricator__add_differential_comment(revision_id="67890", comment="LGTM!")')
        print()
        print("Press Ctrl+C to stop the server")

        try:
            # Run the stdio server
            subprocess.run(
                [python_exe, str(src_dir / "servers" / "stdio_server.py")], env=env, check=True
            )
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except subprocess.CalledProcessError as e:
            print(f"Error starting server: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Phabricator MCP Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="http",
        help="Server mode: http (default) or stdio",
    )
    args = parser.parse_args()

    print("Phabricator MCP Server Setup & Start")
    print("=" * 40)

    # Check environment file
    check_env_file()

    # Setup environment
    if not setup_environment():
        print("Failed to setup environment")
        sys.exit(1)

    print("Environment setup complete!")
    print()

    # Start server
    if not start_server(mode=args.mode):
        sys.exit(1)


if __name__ == "__main__":
    main()
