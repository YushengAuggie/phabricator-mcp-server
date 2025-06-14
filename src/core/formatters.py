"""Output formatting utilities for Phabricator data."""

from typing import Any, Dict, List


def format_task_details(task: Dict[str, Any], comments: List[Dict[str, Any]]) -> str:
    """Format task details for display.

    Args:
        task: Task data from Phabricator API
        comments: List of comment data

    Returns:
        Formatted string representation of task details
    """
    try:
        # Handle both newer API format (with 'fields') and older API format (direct properties)
        if 'fields' in task:
            # Newer API format
            title = task['fields'].get('name', 'No title')
            status = task['fields'].get('status', {}).get('name', 'Unknown status')
            priority = task['fields'].get('priority', {}).get('name', 'Unknown priority')
            description = task['fields'].get('description', {}).get('raw', 'No description')
            task_id = task.get('id', 'Unknown')
        else:
            # Older API format
            title = task.get('title', 'No title')
            status = task.get('statusName', 'Unknown status')
            priority = task.get('priorityName', 'Unknown priority')
            description = task.get('description', 'No description')
            task_id = task.get('id', 'Unknown')

        return f"""
Task T{task_id}: {title}
Status: {status}
Priority: {priority}

Description:
{description}

Comments:
{format_comments(comments)}
        """.strip()
    except KeyError as e:
        return f"Error formatting task details: Missing field {str(e)}"


def format_differential_details(revision: Dict[str, Any], comments: List[Dict[str, Any]]) -> str:
    """Format differential revision details for display.

    Args:
        revision: Revision data from Phabricator API
        comments: List of comment data

    Returns:
        Formatted string representation of revision details
    """
    try:
        # Handle both newer API format (with 'fields') and older API format (direct properties)
        if 'fields' in revision:
            # Newer API format
            title = revision['fields'].get('title', 'No title')
            status = revision['fields'].get('status', {}).get('name', 'Unknown status')
            author = revision['fields'].get('authorPHID', 'Unknown author')
            summary = revision['fields'].get('summary', 'No summary')
            revision_id = revision.get('id', 'Unknown')
        else:
            # Older API format
            title = revision.get('title', 'No title')
            status = revision.get('statusName', 'Unknown status')
            author = revision.get('authorPHID', 'Unknown author')
            summary = revision.get('summary', 'No summary')
            revision_id = revision.get('id', 'Unknown')

        return f"""
Revision D{revision_id}: {title}
Status: {status}
Author: {author}

Summary:
{summary}

Comments:
{format_comments(comments)}
        """.strip()
    except KeyError as e:
        return f"Error formatting revision details: Missing field {str(e)}"


def format_comments(comments: List[Dict[str, Any]]) -> str:
    """Format comments for display.

    Args:
        comments: List of comment dictionaries

    Returns:
        Formatted string representation of comments
    """
    if not comments:
        return "No comments"

    formatted_comments = []
    for comment in comments:
        comment_type = comment.get('type', 'unknown')
        content = comment.get('comments', comment.get('comment', 'No comment content'))
        author = comment.get('authorPHID', 'Unknown author')

        if comment_type == 'accept':
            formatted_comments.append(f"✅ {author}: ACCEPTED")
        elif comment_type == 'reject' or comment_type == 'request-changes':
            formatted_comments.append(f"❌ {author}: REQUESTED CHANGES")
            if content and content != 'No comment content':
                formatted_comments.append(f"   Comment: {content}")
        elif comment_type == 'inline':
            file_path = comment.get('file', 'Unknown file')
            line_num = comment.get('line', 'Unknown line')
            formatted_comments.append(f"💬 {author} (inline in {file_path}:{line_num}): {content}")
        else:
            formatted_comments.append(f"💬 {author}: {content}")

    return "\n\n".join(formatted_comments)


def format_code_changes(changes: List[Dict[str, Any]]) -> str:
    """Format code changes for display.

    Args:
        changes: List of file changes from differential

    Returns:
        Formatted string representation of code changes
    """
    if not changes:
        return "No code changes"

    formatted_changes = []
    for change in changes:
        old_path = change.get('oldPath', '')
        new_path = change.get('currentPath', '')
        change_type = change.get('type', 'unknown')

        # File header
        if change_type == 'add':
            formatted_changes.append(f"📁 NEW FILE: {new_path}")
        elif change_type == 'delete':
            formatted_changes.append(f"🗑️  DELETED: {old_path}")
        elif change_type == 'change':
            formatted_changes.append(f"📝 MODIFIED: {new_path}")
        elif change_type == 'move':
            formatted_changes.append(f"📂 MOVED: {old_path} → {new_path}")
        else:
            formatted_changes.append(f"🔄 {change_type.upper()}: {new_path}")

        # Show hunks if available
        hunks = change.get('hunks', [])
        if hunks:
            for i, hunk in enumerate(hunks[:3]):  # Limit to first 3 hunks
                old_offset = hunk.get('oldOffset', 0)
                new_offset = hunk.get('newOffset', 0)
                old_length = hunk.get('oldLength', 0)
                new_length = hunk.get('newLength', 0)

                formatted_changes.append(
                    f"  @@ -{old_offset},{old_length} +{new_offset},{new_length} @@"
                )

                # Show first few lines of the hunk
                corpus = hunk.get('corpus', '')
                lines = corpus.split('\n')[:10]  # Limit to first 10 lines
                for line in lines:
                    if line.startswith('+'):
                        formatted_changes.append(f"  {line}")
                    elif line.startswith('-'):
                        formatted_changes.append(f"  {line}")
                    elif line.strip():
                        formatted_changes.append(f"   {line}")

                if len(corpus.split('\n')) > 10:
                    formatted_changes.append("  ... (truncated)")

            if len(hunks) > 3:
                formatted_changes.append(f"  ... and {len(hunks) - 3} more hunks")

        formatted_changes.append("")  # Empty line between files

    return "\n".join(formatted_changes)


def format_detailed_differential(
    revision: Dict[str, Any], comments: List[Dict[str, Any]], code_changes: Dict[str, Any]
) -> str:
    """Format comprehensive differential review information.

    Args:
        revision: Revision data from Phabricator API
        comments: List of comment data
        code_changes: Code changes data

    Returns:
        Formatted string with complete review information
    """
    # Basic revision info
    basic_info = format_differential_details(revision, comments)

    # Code changes
    changes_section = ""
    if code_changes and code_changes.get('changes'):
        changes_section = f"""

CODE CHANGES:
============
Diff ID: {code_changes.get('diff_id', 'Unknown')}
Author: {code_changes.get('author', 'Unknown')}

{format_code_changes(code_changes.get('changes', []))}"""

    return basic_info + changes_section
