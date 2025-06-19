"""Output formatting utilities for Phabricator data."""

from typing import Any, Dict, List


def _get_field(data: Dict[str, Any], new_field: str, old_field: str, default: str) -> str:
    """Get field value from either new API format (with 'fields') or old format."""
    if 'fields' in data:
        # Navigate nested fields like 'status.name'
        value = data['fields']
        for key in new_field.split('.'):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return str(value) if value is not None else default
    return str(data.get(old_field, default))


def format_task_details(task: Dict[str, Any], comments: List[Dict[str, Any]] = None) -> str:
    """Format task with full details."""
    task_id = task.get('id', 'Unknown')
    title = _get_field(task, 'name', 'title', 'No title')
    status = _get_field(task, 'status.name', 'statusName', 'Unknown status')
    priority = _get_field(task, 'priority.name', 'priorityName', 'Unknown priority')
    description = _get_field(task, 'description.raw', 'description', 'No description')

    result = f"""Task T{task_id}: {title}
Status: {status}
Priority: {priority}

Description:
{description}"""

    if comments:
        result += f"\n\nComments:\n{format_comments(comments)}"

    return result


def format_differential_details(
    revision: Dict[str, Any], comments: List[Dict[str, Any]] = None
) -> str:
    """Format differential revision with full details."""
    revision_id = revision.get('id', 'Unknown')
    title = _get_field(revision, 'title', 'title', 'No title')
    status = _get_field(revision, 'status.name', 'statusName', 'Unknown status')
    author = _get_field(revision, 'authorPHID', 'authorPHID', 'Unknown author')
    summary = _get_field(revision, 'summary', 'summary', 'No summary')

    result = f"""Revision D{revision_id}: {title}
Status: {status}
Author: {author}

Summary:
{summary}"""

    if comments:
        result += f"\n\nComments:\n{format_comments(comments)}"

    return result


def format_comments(comments: List[Dict[str, Any]]) -> str:
    """Format comments for display."""
    if not comments:
        return "No comments"

    formatted = []
    for comment in comments:
        # Handle both 'type' (new format) and 'action' (Phabricator API format)
        comment_type = comment.get('type', comment.get('action', 'unknown'))

        # Handle different content field names
        content = comment.get('content') or comment.get('comments') or comment.get('comment') or ''

        author = comment.get('authorPHID', 'Unknown author')

        # Skip empty comments (system actions without content)
        if not content and comment_type in ('comment', 'unknown'):
            continue

        if comment_type == 'accept':
            formatted.append(f"✅ {author}: ACCEPTED")
        elif comment_type in ('reject', 'request-changes'):
            formatted.append(f"❌ {author}: REQUESTED CHANGES")
            if content:
                formatted.append(f"   Comment: {content}")
        elif comment_type == 'inline':
            file_path = comment.get('file', 'Unknown file')
            line_num = comment.get('line', '?')
            formatted.append(f"💬 {author} (inline {file_path}:{line_num}): {content}")
        elif content:  # Only show comments that have actual content
            formatted.append(f"💬 {author}: {content}")

    return "\n\n".join(formatted)


def format_code_changes(changes: List[Dict[str, Any]]) -> str:
    """Format code changes for display."""
    if not changes:
        return "No code changes"

    formatted = []
    for change in changes:
        old_path = change.get('oldPath', '')
        new_path = change.get('currentPath', '')
        change_type = change.get('type', 'unknown')

        # File header with emoji
        type_map = {
            'add': f"📁 NEW: {new_path}",
            'delete': f"🗑️ DELETED: {old_path}",
            'change': f"📝 MODIFIED: {new_path}",
            'move': f"📂 MOVED: {old_path} → {new_path}",
        }
        formatted.append(type_map.get(change_type, f"🔄 {change_type.upper()}: {new_path}"))

        # Show limited hunks
        hunks = change.get('hunks', [])[:3]  # Max 3 hunks
        for hunk in hunks:
            old_offset, old_length = hunk.get('oldOffset', 0), hunk.get('oldLength', 0)
            new_offset, new_length = hunk.get('newOffset', 0), hunk.get('newLength', 0)
            formatted.append(f"  @@ -{old_offset},{old_length} +{new_offset},{new_length} @@")

            # Show limited lines
            lines = hunk.get('corpus', '').split('\n')[:10]  # Max 10 lines
            for line in lines:
                if line.startswith(('+', '-')):
                    formatted.append(f"  {line}")
                elif line.strip():
                    formatted.append(f"   {line}")

            if len(hunk.get('corpus', '').split('\n')) > 10:
                formatted.append("  ... (truncated)")

        if len(change.get('hunks', [])) > 3:
            formatted.append(f"  ... and {len(change.get('hunks', [])) - 3} more hunks")

        formatted.append("")  # Empty line between files

    return "\n".join(formatted)


def format_differential_with_code(
    revision: Dict[str, Any],
    comments: List[Dict[str, Any]] = None,
    code_changes: Dict[str, Any] = None,
) -> str:
    """Format differential with code changes."""
    basic_info = format_differential_details(revision, comments)

    if not code_changes or not code_changes.get('changes'):
        return basic_info

    changes_section = f"""

CODE CHANGES:
============
Diff ID: {code_changes.get('diff_id', 'Unknown')}
Author: {code_changes.get('author', 'Unknown')}

{format_code_changes(code_changes.get('changes', []))}"""

    return basic_info + changes_section


# Enhanced formatters for displaying comments with code context
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
        # Handle both 'type' (new format) and 'action' (Phabricator API format)
        comment_type = comment.get('type', comment.get('action', 'unknown'))

        # Get content to filter out empty system actions
        content = comment.get('content') or comment.get('comments') or comment.get('comment') or ''

        # Skip empty comments (system actions without content)
        if not content and comment_type in ('comment', 'unknown'):
            continue

        if comment_type == 'inline':
            inline_comments.append(comment)
        elif comment_type in ('accept', 'reject', 'request-changes'):
            review_actions.append(comment)
        elif content:  # Only include comments with actual content
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
    action_type = action.get('type', action.get('action', 'unknown'))
    author = action.get('authorPHID', 'Unknown author')
    content = action.get('content') or action.get('comments') or action.get('comment') or ''

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
    content = (
        comment.get('content')
        or comment.get('comments')
        or comment.get('comment')
        or 'No comment content'
    )
    return f"💬 {author}:\n   {content}"


def _format_inline_comment_with_context(comment: Dict[str, Any]) -> str:
    """Format an inline comment with code context if available."""
    author = comment.get('authorPHID', 'Unknown author')
    content = (
        comment.get('content')
        or comment.get('comments')
        or comment.get('comment')
        or 'No comment content'
    )
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


def format_review_feedback_with_context(feedback_data: Dict[str, Any]) -> str:
    """Format review feedback with intelligent code context for addressing comments.

    Args:
        feedback_data: Data from get_review_feedback_with_code_context()

    Returns:
        Formatted string optimized for understanding and addressing review feedback
    """
    revision = feedback_data.get('revision', {})
    review_feedback = feedback_data.get('review_feedback', [])
    summary = feedback_data.get('summary', '')
    total_comments = feedback_data.get('total_comments', 0)
    comments_with_context = feedback_data.get('comments_with_context', 0)

    # Header with revision info
    revision_id = revision.get('id', 'Unknown')
    title = _get_field(revision, 'title', 'title', 'No title')
    status = _get_field(revision, 'status.name', 'statusName', 'Unknown status')

    result = [
        f"🔍 Review Feedback Analysis for D{revision_id}",
        f"Title: {title}",
        f"Status: {status}",
        "=" * 80,
        "",
        summary,
        "",
        "=" * 80,
    ]

    if not review_feedback:
        result.append("✅ No actionable review feedback found!")
        return "\n".join(result)

    # Group feedback by type and priority
    nits = []
    issues = []
    suggestions = []
    other = []

    for feedback in review_feedback:
        comment_lower = feedback['comment'].lower()
        if 'nit' in comment_lower:
            nits.append(feedback)
        elif any(word in comment_lower for word in ['error', 'bug', 'issue', 'problem']):
            issues.append(feedback)
        elif any(word in comment_lower for word in ['suggest', 'recommend', 'consider']):
            suggestions.append(feedback)
        else:
            other.append(feedback)

    # Sort each category by whether they have code context (prioritize those with context)
    def sort_key(f):
        return (0 if f.get('code_context') else 1, f['comment'])

    issues.sort(key=sort_key)
    suggestions.sort(key=sort_key)
    nits.sort(key=sort_key)
    other.sort(key=sort_key)

    # Display by priority: issues, suggestions, nits, other
    sections = [
        ("🚨 ISSUES TO FIX", issues),
        ("💡 SUGGESTIONS", suggestions),
        ("🔧 NITS & STYLE", nits),
        ("📝 OTHER FEEDBACK", other),
    ]

    for section_title, feedback_list in sections:
        if not feedback_list:
            continue

        result.append(f"\n{section_title} ({len(feedback_list)} items)")
        result.append("=" * len(section_title))

        for i, feedback in enumerate(feedback_list, 1):
            result.append(f"\n{i}. {_format_feedback_item(feedback)}")

    # Add actionable summary
    result.append("\n" + "=" * 80)
    result.append("📋 ACTION ITEMS:")

    action_items = []
    for feedback in review_feedback:
        if feedback.get('code_context'):
            file_path = feedback.get('primary_file', 'Unknown file')
            line_num = feedback.get('primary_line', '?')
            action_items.append(f"• {file_path}:{line_num} - {feedback['comment'][:60]}...")
        else:
            action_items.append(f"• General: {feedback['comment'][:60]}...")

    if action_items:
        result.extend(action_items)
    else:
        result.append("• Review feedback received but no specific action items identified")

    return "\n".join(result)


def _format_feedback_item(feedback: Dict[str, Any]) -> str:
    """Format an individual feedback item with context."""
    comment = feedback['comment']
    author = feedback.get('author', 'unknown')
    feedback_type = feedback.get('type', 'general')

    parts = [f"💬 {author}: {comment}"]

    # Add code context if available
    if feedback.get('code_context'):
        context = feedback['code_context']
        file_path = context.get('file', 'Unknown file')
        target_line = context.get('target_line', '?')

        parts.append(f"\n   📍 Location: {file_path}:{target_line}")
        parts.append(f"   {context.get('hunk_info', '')}")
        parts.append("   " + "-" * 50)

        # Show code with highlighting
        for line_info in context.get('lines', []):
            line_num = str(line_info['line_number']).rjust(4)
            content = line_info['content']

            if line_info.get('is_highlighted') or line_info.get('is_target'):
                marker = ">>> "
                # Highlight the specific line that's being commented on
                parts.append(f"   {marker}{line_num} | {content}  ⟵ COMMENTED LINE")
            else:
                marker = "    "
                line_type = line_info.get('type', 'context')
                if line_type == 'added':
                    marker = "+   "
                elif line_type == 'removed':
                    marker = "-   "
                parts.append(f"   {marker}{line_num} | {content}")

        parts.append("   " + "-" * 50)

        # Add suggestions for similar locations if available
        if feedback.get('suggested_locations'):
            parts.append("   💡 Also check similar code at:")
            for loc in feedback['suggested_locations'][:2]:  # Show max 2 suggestions
                parts.append(f"      • {loc['file']}:{loc['line']} - {loc['line_content'][:40]}...")

    return "\n".join(parts)
