#!/usr/bin/env python3
"""Demonstration of enhanced comment retrieval with code context.

This script shows how to:
1. Retrieve all comments (general and inline) from a revision
2. Get the surrounding code context for inline comments
3. Display them in an organized, easy-to-review format
"""

import asyncio
import os
from typing import Optional

from src.core.enhanced_client import EnhancedPhabricatorClient
from src.core.enhanced_formatters import format_enhanced_differential


async def demo_review_comments(revision_id: Optional[str] = None):
    """Demonstrate retrieving and displaying review comments with context.

    Args:
        revision_id: Differential revision ID (without 'D' prefix)
                    If not provided, will prompt for input
    """
    # Initialize client
    print("Initializing Phabricator client...")

    # For demo purposes, we'll mock the environment variables
    # In real usage, these should be set in .env file
    if not os.getenv("PHABRICATOR_TOKEN"):
        print("\nNote: PHABRICATOR_TOKEN not set. This demo requires:")
        print("1. Copy .env.example to .env")
        print("2. Add your Phabricator API token")
        print("3. Set your Phabricator instance URL")
        return

    try:
        client = EnhancedPhabricatorClient()
    except Exception as e:
        print(f"Error: {e}")
        return

    # Get revision ID if not provided
    if not revision_id:
        revision_id = input("\nEnter revision ID (e.g., 111 for D111): ").strip()

    print(f"\nRetrieving revision D{revision_id} with enhanced comment context...")
    print("=" * 80)

    try:
        # Get all data with enhanced context
        result = await client.get_revision_comments_with_context(
            revision_id=revision_id, context_lines=5  # Show 5 lines before/after inline comments
        )

        # Format and display
        formatted_output = format_enhanced_differential(
            revision=result['revision'],
            comments=result['comments'],
            code_changes=result['code_changes'],
        )

        print(formatted_output)

        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print(f"Total comments: {len(result['comments'])}")

        inline_count = sum(1 for c in result['comments'] if c.get('type') == 'inline')
        general_count = sum(1 for c in result['comments'] if c.get('type') == 'comment')
        review_count = sum(
            1
            for c in result['comments']
            if c.get('type') in ('accept', 'reject', 'request-changes')
        )

        print(f"  - Inline comments: {inline_count}")
        print(f"  - General comments: {general_count}")
        print(f"  - Review actions: {review_count}")

        # Check how many inline comments have context
        context_count = sum(
            1 for c in result['comments'] if c.get('type') == 'inline' and 'code_context' in c
        )
        if inline_count > 0:
            print(f"  - Inline comments with code context: {context_count}/{inline_count}")

    except Exception as e:
        print(f"\nError retrieving revision: {e}")


async def demo_add_inline_comment():
    """Demonstrate adding an inline comment to a revision."""
    print("\nDEMO: Adding inline comment")
    print("=" * 80)

    # This is a demonstration of how the API would work
    client = EnhancedPhabricatorClient()

    # Example usage (would need real values):
    revision_id = input("Enter revision ID: ").strip()
    file_path = input("Enter file path: ").strip()
    line_number = int(input("Enter line number: ").strip())
    comment_text = input("Enter comment: ").strip()

    try:
        result = await client.add_inline_comment(
            revision_id=revision_id,
            file_path=file_path,
            line_number=line_number,
            content=comment_text,
        )
        print(f"\nComment added successfully: {result}")
    except NotImplementedError:
        print("\nNote: Adding inline comments requires specific Phabricator API configuration.")
        print("The exact implementation depends on your Phabricator instance version.")
    except Exception as e:
        print(f"\nError: {e}")


async def main():
    """Main demo function."""
    print("Phabricator Enhanced Comment Retrieval Demo")
    print("=" * 80)

    while True:
        print("\nOptions:")
        print("1. View revision with enhanced comments (e.g., D111)")
        print("2. Demo: Add inline comment (requires API setup)")
        print("3. Exit")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            await demo_review_comments()
        elif choice == "2":
            await demo_add_inline_comment()
        elif choice == "3":
            print("\nExiting...")
            break
        else:
            print("\nInvalid option. Please try again.")


if __name__ == "__main__":
    print("\nExample: To test with D111, enter '111' when prompted")
    asyncio.run(main())
