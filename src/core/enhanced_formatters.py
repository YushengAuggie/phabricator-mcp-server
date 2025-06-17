"""Enhanced formatters for displaying comments with code context."""

from typing import Any, Dict, List

from .formatters import format_code_changes, format_differential_details


def format_comments_with_context(comments: List[Dict[str, Any]]) -> str:
    """Format comments with code context for inline comments.

    Args:
        comments: List of comment dictionaries (potentially enhanced)

    Returns:
        Formatted string with enhanced comment display
    """
    if not comments:
        return "No comments"

    # Group comments by type
    general_comments = []
    inline_comments = []
    review_actions = []

    for comment in comments:
        comment_type = comment.get('type', 'unknown')
        if comment_type == 'inline':
            inline_comments.append(comment)
        elif comment_type in ('accept', 'reject', 'request-changes'):
            review_actions.append(comment)
        else:
            general_comments.append(comment)

    sections = []

    # Format review actions first
    if review_actions:
        sections.append("REVIEW ACTIONS:")
        sections.append("=" * 50)
        for action in review_actions:
            sections.append(_format_review_action(action))
        sections.append("")

    # Format general comments
    if general_comments:
        sections.append("GENERAL COMMENTS:")
        sections.append("=" * 50)
        for comment in general_comments:
            sections.append(_format_general_comment(comment))
        sections.append("")

    # Format inline comments with context
    if inline_comments:
        sections.append("INLINE COMMENTS:")
        sections.append("=" * 50)

        # Group by file
        by_file = {}
        for comment in inline_comments:
            file_path = (
                comment.get('enhanced_file')
                or comment.get('file')
                or comment.get('path', 'Unknown file')
            )
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(comment)

        # Sort files and comments within files
        for file_path in sorted(by_file.keys()):
            sections.append(f"\n📁 {file_path}")
            sections.append("-" * (len(file_path) + 4))

            # Sort comments by line number
            file_comments = sorted(
                by_file[file_path], key=lambda c: c.get('enhanced_line', c.get('line', 0))
            )

            for comment in file_comments:
                sections.append(_format_inline_comment_with_context(comment))

    return "\n".join(sections)


def _format_review_action(action: Dict[str, Any]) -> str:
    """Format a review action (accept/reject)."""
    action_type = action.get('type', 'unknown')
    author = action.get('authorPHID', 'Unknown author')
    content = action.get('comments', action.get('comment', ''))

    if action_type == 'accept':
        result = f"✅ {author}: ACCEPTED"
    elif action_type in ('reject', 'request-changes'):
        result = f"❌ {author}: REQUESTED CHANGES"
    else:
        result = f"🔄 {author}: {action_type.upper()}"

    if content and content != 'No comment content':
        result += f"\n   Comment: {content}"

    return result


def _format_general_comment(comment: Dict[str, Any]) -> str:
    """Format a general comment."""
    author = comment.get('authorPHID', 'Unknown author')
    content = comment.get('comments', comment.get('comment', 'No comment content'))
    return f"💬 {author}:\n   {content}"


def _format_inline_comment_with_context(comment: Dict[str, Any]) -> str:
    """Format an inline comment with code context if available."""
    author = comment.get('authorPHID', 'Unknown author')
    content = comment.get('comments', comment.get('comment', 'No comment content'))
    line_num = comment.get('enhanced_line', comment.get('line', 'Unknown line'))

    parts = [f"\n  Line {line_num} - {author}:"]

    # Add code context if available
    if 'code_context' in comment and comment['code_context']:
        context = comment['code_context']
        parts.append(f"  {context['hunk_info']}")
        parts.append("  " + "-" * 60)

        for line_info in context['lines']:
            line_marker = ">>>" if line_info['is_target'] else "   "
            line_content = line_info['content']
            line_num_str = str(line_info['line_number']).rjust(4)
            parts.append(f"  {line_marker} {line_num_str} | {line_content}")

        parts.append("  " + "-" * 60)

    # Add the comment text
    parts.append(f"  💬 {content}")

    return "\n".join(parts)


def format_enhanced_differential(
    revision: Dict[str, Any], comments: List[Dict[str, Any]], code_changes: Dict[str, Any]
) -> str:
    """Format comprehensive differential review with enhanced comments.

    Args:
        revision: Revision data
        comments: Enhanced comment data
        code_changes: Code changes data

    Returns:
        Formatted string with complete review information
    """
    # Basic revision info
    basic_info = format_differential_details(revision, [])  # Empty comments, we'll add our own

    # Enhanced comments section
    comments_section = f"""

REVIEW FEEDBACK:
===============
{format_comments_with_context(comments)}"""

    # Code changes section
    changes_section = ""
    if code_changes and code_changes.get('changes'):
        changes_section = f"""

CODE CHANGES:
============
Diff ID: {code_changes.get('diff_id', 'Unknown')}
Author: {code_changes.get('author', 'Unknown')}

{format_code_changes(code_changes.get('changes', []))}"""

    return basic_info.replace("\nComments:\nNo comments", "") + comments_section + changes_section

