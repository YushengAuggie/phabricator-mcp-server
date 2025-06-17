#!/usr/bin/env python3
"""Fetch revision comments using web scraping as fallback."""

import os

from dotenv import load_dotenv


def fetch_revision_web():
    """Try to understand the revision structure via web."""
    load_dotenv()

    revision_id = "111"
    base_url = os.getenv("PHABRICATOR_URL").replace("/api/", "")
    revision_url = f"{base_url}/D{revision_id}"

    print(f"Revision URL: {revision_url}")
    print("\nTo properly retrieve comments with code context, the Phabricator instance needs to:")
    print("1. Have the transaction.search API enabled (for newer versions)")
    print("2. Or use differential.getinlinecomments API (for inline comments)")
    print("3. Or parse the web interface directly")

    print(
        "\nBased on the API tests, your Phabricator instance appears to be using an older version"
    )
    print("that doesn't expose comment content through the standard APIs we tried.")

    print("\nPossible solutions:")
    print("1. Use the web interface to manually review comments")
    print("2. Check if your Phabricator instance has custom APIs for comments")
    print("3. Upgrade Phabricator to a newer version with better API support")

    # Show what we CAN get
    print("\nWhat we CAN retrieve:")
    print("- Revision metadata (title, status, author)")
    print("- Code changes/diffs")
    print("- Comment transactions (but without content in this version)")
    print("- File changes and diff hunks")


if __name__ == "__main__":
    fetch_revision_web()

