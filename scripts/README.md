# Scripts

This directory contains utility and debug scripts for development and testing of the Phabricator MCP Server.

## Debug Scripts

- **debug_comments.py** - Examines raw comment data structures from the Phabricator API
- **fetch_revision_web.py** - Explores alternative methods for fetching revision data

## Test Scripts

These are manual test scripts (not pytest tests) used during development:

- **test_api_direct.py** - Direct testing of Phabricator API methods to understand data structures
- **test_inline_comments.py** - Tests inline comment retrieval functionality
- **test_revision_example.py** - Tests enhanced comment retrieval for a sample revision (D111)

## Usage

These scripts are meant for development and debugging purposes only. They require proper environment setup:

```bash
# Set up environment variables
export PHABRICATOR_TOKEN=your-token
export PHABRICATOR_URL=https://your-instance.com/api/

# Run a script
python scripts/debug_comments.py
```

## Note

These scripts are not part of the production system and may contain experimental or incomplete code. They are preserved for reference and debugging purposes.