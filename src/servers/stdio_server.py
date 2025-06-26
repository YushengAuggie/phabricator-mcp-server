"""Stdio server implementation for MCP compatibility."""

import asyncio
import os

import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from core.client import PhabricatorAPIError, PhabricatorClient
from core.formatters import (
    format_differential_details,
    format_review_feedback_with_context,
    format_task_details,
)

# Load environment variables from .env file
load_dotenv()


class PhabricatorMCPServer:
    """MCP Server implementation using stdio transport."""

    def __init__(self):
        """Initialize the server."""
        self.server = Server("phabricator-mcp-server")
        self.phab_client = None
        self.setup_handlers()

    def _get_phab_client(self) -> PhabricatorClient:
        """Get or create the Phabricator client lazily."""
        if self.phab_client is None:
            token = os.getenv("PHABRICATOR_TOKEN")
            if not token:
                raise ValueError("PHABRICATOR_TOKEN environment variable is required")
            self.phab_client = PhabricatorClient(token=token)
        return self.phab_client

    def setup_handlers(self):
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="get-task",
                    description="Get details of a Phabricator task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID (without 'T' prefix)",
                            }
                        },
                        "required": ["task_id"],
                    },
                ),
                types.Tool(
                    name="add-task-comment",
                    description="Add a comment to a Phabricator task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID (without 'T' prefix)",
                            },
                            "comment": {"type": "string", "description": "Comment text to add"},
                        },
                        "required": ["task_id", "comment"],
                    },
                ),
                types.Tool(
                    name="subscribe-to-task",
                    description="Subscribe users to a Phabricator task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID (without 'T' prefix)",
                            },
                            "user_phids": {
                                "type": "string",
                                "description": "Comma-separated list of user PHIDs to subscribe",
                            },
                        },
                        "required": ["task_id", "user_phids"],
                    },
                ),
                types.Tool(
                    name="get-differential-detailed",
                    description="Get detailed code review information including comments and code changes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            }
                        },
                        "required": ["revision_id"],
                    },
                ),
                types.Tool(
                    name="get-differential",
                    description="Get details of a Phabricator differential revision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            }
                        },
                        "required": ["revision_id"],
                    },
                ),
                types.Tool(
                    name="add-differential-comment",
                    description="Add a comment to a differential revision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            },
                            "comment": {"type": "string", "description": "Comment text to add"},
                        },
                        "required": ["revision_id", "comment"],
                    },
                ),
                types.Tool(
                    name="accept-differential",
                    description="Accept a differential revision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            }
                        },
                        "required": ["revision_id"],
                    },
                ),
                types.Tool(
                    name="request-changes-differential",
                    description="Request changes on a differential revision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            },
                            "comment": {
                                "type": "string",
                                "description": "Optional comment explaining the requested changes",
                            },
                        },
                        "required": ["revision_id"],
                    },
                ),
                types.Tool(
                    name="subscribe-to-differential",
                    description="Subscribe users to a differential revision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            },
                            "user_phids": {
                                "type": "string",
                                "description": "Comma-separated list of user PHIDs to subscribe",
                            },
                        },
                        "required": ["revision_id", "user_phids"],
                    },
                ),
                types.Tool(
                    name="get-review-feedback",
                    description="Get review feedback with intelligent code context for addressing comments. Perfect for understanding what needs to be changed and where to change it.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            },
                            "context_lines": {
                                "type": "string",
                                "description": "Number of lines of code context to show around each comment (default: 7)",
                            },
                        },
                        "required": ["revision_id"],
                    },
                ),
                types.Tool(
                    name="add-inline-comment",
                    description="Add an inline comment to a specific line in a differential revision. Perfect for automated code review or targeted feedback.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "revision_id": {
                                "type": "string",
                                "description": "Revision ID (without 'D' prefix)",
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to comment on",
                            },
                            "line_number": {
                                "type": "string",
                                "description": "Line number to comment on",
                            },
                            "content": {"type": "string", "description": "Comment text to add"},
                            "is_new_file": {
                                "type": "string",
                                "description": "Whether to comment on the new version (true) or old version (false) of the file (default: true)",
                            },
                        },
                        "required": ["revision_id", "file_path", "line_number", "content"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            try:
                if name == "get-task":
                    phab_client = self._get_phab_client()
                    task = await phab_client.get_task(arguments["task_id"])
                    comments = await phab_client.get_task_comments(arguments["task_id"])

                    return [
                        types.TextContent(type="text", text=format_task_details(task, comments))
                    ]

                elif name == "add-task-comment":
                    phab_client = self._get_phab_client()
                    await phab_client.add_task_comment(arguments["task_id"], arguments["comment"])
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Comment added successfully to task T{arguments['task_id']}",
                        )
                    ]

                elif name == "subscribe-to-task":
                    user_phids = arguments["user_phids"]
                    if isinstance(user_phids, str):
                        user_phids = [
                            phid.strip() for phid in user_phids.split(',') if phid.strip()
                        ]

                    phab_client = self._get_phab_client()
                    await phab_client.subscribe_to_task(arguments["task_id"], user_phids)
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ {len(user_phids)} user(s) subscribed successfully to task T{arguments['task_id']}",
                        )
                    ]

                elif name == "get-differential-detailed":
                    phab_client = self._get_phab_client()
                    revision = await phab_client.get_differential_revision(arguments["revision_id"])
                    comments = await phab_client.get_differential_comments(arguments["revision_id"])
                    code_changes = await phab_client.get_differential_code_changes(
                        arguments["revision_id"]
                    )

                    from core.formatters import format_enhanced_differential

                    return [
                        types.TextContent(
                            type="text",
                            text=format_enhanced_differential(revision, comments, code_changes),
                        )
                    ]

                elif name == "get-differential":
                    phab_client = self._get_phab_client()
                    revision = await phab_client.get_differential_revision(arguments["revision_id"])
                    comments = await phab_client.get_differential_comments(arguments["revision_id"])

                    return [
                        types.TextContent(
                            type="text", text=format_differential_details(revision, comments)
                        )
                    ]

                elif name == "add-differential-comment":
                    phab_client = self._get_phab_client()
                    await phab_client.add_differential_comment(
                        arguments["revision_id"], arguments["comment"]
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Comment added successfully to revision D{arguments['revision_id']}",
                        )
                    ]

                elif name == "accept-differential":
                    phab_client = self._get_phab_client()
                    await phab_client.accept_differential_revision(arguments["revision_id"])
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Revision D{arguments['revision_id']} accepted successfully",
                        )
                    ]

                elif name == "request-changes-differential":
                    phab_client = self._get_phab_client()
                    await phab_client.request_changes_differential_revision(
                        arguments["revision_id"], arguments.get("comment")
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Changes requested for revision D{arguments['revision_id']}",
                        )
                    ]

                elif name == "subscribe-to-differential":
                    user_phids = arguments["user_phids"]
                    if isinstance(user_phids, str):
                        user_phids = [
                            phid.strip() for phid in user_phids.split(',') if phid.strip()
                        ]

                    phab_client = self._get_phab_client()
                    await phab_client.subscribe_to_differential(
                        arguments["revision_id"], user_phids
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ {len(user_phids)} user(s) subscribed successfully to revision D{arguments['revision_id']}",
                        )
                    ]

                elif name == "get-review-feedback":
                    phab_client = self._get_phab_client()
                    context_lines = int(arguments.get("context_lines", 7))
                    feedback_data = await phab_client.get_review_feedback_with_code_context(
                        arguments["revision_id"], context_lines
                    )

                    return [
                        types.TextContent(
                            type="text", text=format_review_feedback_with_context(feedback_data)
                        )
                    ]

                elif name == "add-inline-comment":
                    line_number = int(arguments["line_number"])
                    is_new_file = arguments.get("is_new_file", "true").lower() in (
                        "true",
                        "1",
                        "yes",
                    )

                    phab_client = self._get_phab_client()
                    await phab_client.add_inline_comment(
                        arguments["revision_id"],
                        arguments["file_path"],
                        line_number,
                        arguments["content"],
                        is_new_file,
                    )

                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Inline comment added successfully to {arguments['file_path']}:{line_number} in revision D{arguments['revision_id']}",
                        )
                    ]

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except PhabricatorAPIError as e:
                return [types.TextContent(type="text", text=f"Phabricator API Error: {str(e)}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Unexpected error: {str(e)}")]

    async def run(self):
        """Run the MCP server with stdio transport."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="phabricator-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


def main():
    """Main entry point for stdio server."""
    try:
        server = PhabricatorMCPServer()
        asyncio.run(server.run())
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
