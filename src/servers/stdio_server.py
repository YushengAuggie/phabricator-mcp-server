"""Stdio server implementation for MCP compatibility."""

import asyncio
import os
from typing import List

import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from core.client import PhabricatorAPIError, PhabricatorClient
from core.formatters import format_differential_details, format_task_details

# Load environment variables from .env file
load_dotenv()


class PhabricatorMCPServer:
    """MCP Server implementation using stdio transport."""

    def __init__(self):
        """Initialize the server."""
        self.server = Server("phabricator-mcp-server")
        token = os.getenv("PHABRICATOR_TOKEN")
        if not token:
            raise ValueError("PHABRICATOR_TOKEN environment variable is required")
        self.phab_client = PhabricatorClient(token=token)
        self.setup_handlers()

    def setup_handlers(self):
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="get-task",
                    description="Get details of a Phabricator task",
                    arguments=[
                        types.ToolArgument(
                            name="task_id",
                            description="Task ID (without 'T' prefix)",
                            required=True,
                        )
                    ],
                ),
                types.Tool(
                    name="add-task-comment",
                    description="Add a comment to a Phabricator task",
                    arguments=[
                        types.ToolArgument(
                            name="task_id",
                            description="Task ID (without 'T' prefix)",
                            required=True,
                        ),
                        types.ToolArgument(
                            name="comment", description="Comment text to add", required=True
                        ),
                    ],
                ),
                types.Tool(
                    name="subscribe-to-task",
                    description="Subscribe users to a Phabricator task",
                    arguments=[
                        types.ToolArgument(
                            name="task_id",
                            description="Task ID (without 'T' prefix)",
                            required=True,
                        ),
                        types.ToolArgument(
                            name="user_phids",
                            description="Comma-separated list of user PHIDs to subscribe",
                            required=True,
                        ),
                    ],
                ),
                types.Tool(
                    name="get-differential",
                    description="Get details of a Phabricator differential revision",
                    arguments=[
                        types.ToolArgument(
                            name="revision_id",
                            description="Revision ID (without 'D' prefix)",
                            required=True,
                        )
                    ],
                ),
                types.Tool(
                    name="add-differential-comment",
                    description="Add a comment to a differential revision",
                    arguments=[
                        types.ToolArgument(
                            name="revision_id",
                            description="Revision ID (without 'D' prefix)",
                            required=True,
                        ),
                        types.ToolArgument(
                            name="comment", description="Comment text to add", required=True
                        ),
                    ],
                ),
                types.Tool(
                    name="accept-differential",
                    description="Accept a differential revision",
                    arguments=[
                        types.ToolArgument(
                            name="revision_id",
                            description="Revision ID (without 'D' prefix)",
                            required=True,
                        )
                    ],
                ),
                types.Tool(
                    name="request-changes-differential",
                    description="Request changes on a differential revision",
                    arguments=[
                        types.ToolArgument(
                            name="revision_id",
                            description="Revision ID (without 'D' prefix)",
                            required=True,
                        ),
                        types.ToolArgument(
                            name="comment",
                            description="Optional comment explaining the requested changes",
                            required=False,
                        ),
                    ],
                ),
                types.Tool(
                    name="subscribe-to-differential",
                    description="Subscribe users to a differential revision",
                    arguments=[
                        types.ToolArgument(
                            name="revision_id",
                            description="Revision ID (without 'D' prefix)",
                            required=True,
                        ),
                        types.ToolArgument(
                            name="user_phids",
                            description="Comma-separated list of user PHIDs to subscribe",
                            required=True,
                        ),
                    ],
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            try:
                if name == "get-task":
                    task = await self.phab_client.get_task(arguments["task_id"])
                    comments = await self.phab_client.get_task_comments(arguments["task_id"])

                    return [
                        types.TextContent(type="text", text=format_task_details(task, comments))
                    ]

                elif name == "add-task-comment":
                    await self.phab_client.add_task_comment(
                        arguments["task_id"], arguments["comment"]
                    )
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

                    await self.phab_client.subscribe_to_task(arguments["task_id"], user_phids)
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ {len(user_phids)} user(s) subscribed successfully to task T{arguments['task_id']}",
                        )
                    ]

                elif name == "get-differential":
                    revision = await self.phab_client.get_differential_revision(
                        arguments["revision_id"]
                    )
                    comments = await self.phab_client.get_differential_comments(
                        arguments["revision_id"]
                    )

                    return [
                        types.TextContent(
                            type="text", text=format_differential_details(revision, comments)
                        )
                    ]

                elif name == "add-differential-comment":
                    await self.phab_client.add_differential_comment(
                        arguments["revision_id"], arguments["comment"]
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Comment added successfully to revision D{arguments['revision_id']}",
                        )
                    ]

                elif name == "accept-differential":
                    await self.phab_client.accept_differential_revision(arguments["revision_id"])
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ Revision D{arguments['revision_id']} accepted successfully",
                        )
                    ]

                elif name == "request-changes-differential":
                    await self.phab_client.request_changes_differential_revision(
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

                    await self.phab_client.subscribe_to_differential(
                        arguments["revision_id"], user_phids
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"✓ {len(user_phids)} user(s) subscribed successfully to revision D{arguments['revision_id']}",
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
