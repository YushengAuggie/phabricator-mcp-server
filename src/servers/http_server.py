#!/usr/bin/env python3
"""HTTP server implementation using FastMCP for better reliability and performance."""

import os
import sys

import dotenv
import fastmcp

# Fix sys.path to avoid conflicts with system phabricator module
# Move virtual environment paths to the front to prioritize them
venv_paths = [p for p in sys.path if 'site-packages' in p]
other_paths = [p for p in sys.path if 'site-packages' not in p]

# Reconstruct sys.path with venv paths first
sys.path = venv_paths + other_paths

from core.client import PhabricatorAPIError, PhabricatorClient
from core.formatters import (
    format_differential_details,
    format_enhanced_differential,
    format_review_feedback_with_context,
    format_task_details,
)

# Load environment variables
dotenv.load_dotenv()


def create_http_server() -> fastmcp.FastMCP:
    """Create and configure the FastMCP HTTP server.

    Returns:
        Configured FastMCP server instance
    """
    # Initialize FastMCP
    mcp = fastmcp.FastMCP("Phabricator MCP Server")

    # Initialize Phabricator client
    token = os.getenv("PHABRICATOR_TOKEN")
    if not token:
        raise ValueError("PHABRICATOR_TOKEN environment variable is required")

    phab_client = PhabricatorClient(token=token)

    @mcp.tool()
    async def get_task(task_id: str) -> str:
        """Get details of a Phabricator task.

        Args:
            task_id: Task ID (without 'T' prefix)

        Returns:
            Formatted task details including description and comments
        """
        try:
            task = await phab_client.get_task(task_id)
            comments = await phab_client.get_task_comments(task_id)
            return format_task_details(task, comments)
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def add_task_comment(task_id: str, comment: str) -> str:
        """Add a comment to a Phabricator task.

        Args:
            task_id: Task ID (without 'T' prefix)
            comment: Comment text to add

        Returns:
            Success message or error description
        """
        try:
            await phab_client.add_task_comment(task_id, comment)
            return f"✓ Comment added successfully to task T{task_id}"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def subscribe_to_task(task_id: str, user_phids: str) -> str:
        """Subscribe users to a Phabricator task.

        Args:
            task_id: Task ID (without 'T' prefix)
            user_phids: Comma-separated list of user PHIDs to subscribe

        Returns:
            Success message or error description
        """
        try:
            phid_list = [phid.strip() for phid in user_phids.split(',') if phid.strip()]
            if not phid_list:
                return "Error: No valid user PHIDs provided"

            await phab_client.subscribe_to_task(task_id, phid_list)
            return f"✓ {len(phid_list)} user(s) subscribed successfully to task T{task_id}"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def get_differential_detailed(revision_id: str) -> str:
        """Get detailed code review information including comments and code changes.

        Args:
            revision_id: Revision ID (without 'D' prefix)

        Returns:
            Comprehensive formatted review details with code changes
        """
        try:
            revision = await phab_client.get_differential_revision(revision_id)
            comments = await phab_client.get_differential_comments(revision_id)
            code_changes = await phab_client.get_differential_code_changes(revision_id)
            return format_enhanced_differential(revision, comments, code_changes)
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def get_differential(revision_id: str) -> str:
        """Get details of a Phabricator differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)

        Returns:
            Formatted revision details including description and comments
        """
        try:
            revision = await phab_client.get_differential_revision(revision_id)
            comments = await phab_client.get_differential_comments(revision_id)
            return format_differential_details(revision, comments)
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def add_differential_comment(revision_id: str, comment: str) -> str:
        """Add a comment to a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            comment: Comment text to add

        Returns:
            Success message or error description
        """
        try:
            await phab_client.add_differential_comment(revision_id, comment)
            return f"✓ Comment added successfully to revision D{revision_id}"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def accept_differential(revision_id: str) -> str:
        """Accept a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)

        Returns:
            Success message or error description
        """
        try:
            await phab_client.accept_differential_revision(revision_id)
            return f"✓ Revision D{revision_id} accepted successfully"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def request_changes_differential(revision_id: str, comment: str = None) -> str:
        """Request changes on a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            comment: Optional comment explaining the requested changes

        Returns:
            Success message or error description
        """
        try:
            await phab_client.request_changes_differential_revision(revision_id, comment)
            return f"✓ Changes requested for revision D{revision_id}"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def subscribe_to_differential(revision_id: str, user_phids: str) -> str:
        """Subscribe users to a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            user_phids: Comma-separated list of user PHIDs to subscribe

        Returns:
            Success message or error description
        """
        try:
            phid_list = [phid.strip() for phid in user_phids.split(',') if phid.strip()]
            if not phid_list:
                return "Error: No valid user PHIDs provided"

            await phab_client.subscribe_to_differential(revision_id, phid_list)
            return f"✓ {len(phid_list)} user(s) subscribed successfully to revision D{revision_id}"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def get_review_feedback(revision_id: str, context_lines: int = 7) -> str:
        """Get review feedback with intelligent code context for addressing comments.

        Perfect for understanding what needs to be changed and where to change it.
        Analyzes comments and correlates them with specific code locations.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            context_lines: Number of lines of code context to show around each comment (default: 7)

        Returns:
            Formatted review feedback with code context and actionable guidance
        """
        try:
            feedback_data = await phab_client.get_review_feedback_with_code_context(
                revision_id, context_lines
            )
            return format_review_feedback_with_context(feedback_data)
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def add_inline_comment(
        revision_id: str, file_path: str, line_number: int, content: str, is_new_file: bool = True
    ) -> str:
        """Add an inline comment to a specific line in a differential revision.

        Perfect for automated code review or targeted feedback on specific lines.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            file_path: Path to the file to comment on
            line_number: Line number to comment on
            content: Comment text to add
            is_new_file: Whether to comment on the new version (True) or old version (False) of the file

        Returns:
            Success message or error description
        """
        try:
            await phab_client.add_inline_comment(
                revision_id, file_path, line_number, content, is_new_file
            )
            return f"✓ Inline comment added successfully to {file_path}:{line_number} in revision D{revision_id}"
        except PhabricatorAPIError as e:
            return f"Phabricator API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    return mcp


def main():
    """Main entry point for running the HTTP server."""
    mcp = create_http_server()

    print("🚀 Starting Phabricator MCP HTTP Server")
    print("📡 Server will be available at: http://localhost:8932")
    print("🔗 MCP Endpoint: http://localhost:8932/sse")
    print()
    print("📋 Add this to your MCP configuration:")
    print('{')
    print('  "mcpServers": {')
    print('    "phabricator": {')
    print('      "url": "http://localhost:8932/sse"')
    print('    }')
    print('  }')
    print('}')
    print()
    print("Available tools:")
    print("• get_task - Get task details")
    print("• add_task_comment - Add comment to task")
    print("• subscribe_to_task - Subscribe users to task")
    print("• get_differential - Get differential revision details")
    print("• get_differential_detailed - Get comprehensive review with code changes")
    print("• get_review_feedback - Get review feedback with intelligent code context")
    print("• add_differential_comment - Add comment to differential")
    print("• add_inline_comment - Add inline comment to specific line (NEW!)")
    print("• accept_differential - Accept differential revision")
    print("• request_changes_differential - Request changes on differential")
    print("• subscribe_to_differential - Subscribe users to differential")
    print()

    # Run with SSE transport on port 8932
    mcp.run(transport="sse", port=8932, host="localhost")


if __name__ == "__main__":
    main()
