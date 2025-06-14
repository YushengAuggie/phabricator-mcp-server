#!/usr/bin/env python3
"""HTTP server implementation using FastMCP for better reliability and performance."""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from core.client import PhabricatorAPIError, PhabricatorClient
from core.formatters import (
    format_detailed_differential,
    format_differential_details,
    format_task_details,
)

# Load environment variables
load_dotenv()


def create_http_server() -> FastMCP:
    """Create and configure the FastMCP HTTP server.

    Returns:
        Configured FastMCP server instance
    """
    # Initialize FastMCP
    mcp = FastMCP("Phabricator MCP Server")

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
            return format_detailed_differential(revision, comments, code_changes)
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
    print("• add_differential_comment - Add comment to differential")
    print("• accept_differential - Accept differential revision")
    print("• request_changes_differential - Request changes on differential")
    print("• subscribe_to_differential - Subscribe users to differential")
    print()

    # Run with SSE transport on port 8932
    mcp.run(transport="sse", port=8932, host="localhost")


if __name__ == "__main__":
    main()
