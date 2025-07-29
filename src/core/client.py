"""Enhanced Phabricator API client with proper error handling and type safety."""

import os
import re
from typing import Any

from .phabricator_compat import create_phabricator_client


class PhabricatorAPIError(Exception):
    """Custom exception for Phabricator API errors."""

    pass


class PhabricatorClient:
    """Enhanced Phabricator API client with comprehensive functionality."""

    def __init__(self, token: str | None = None, host: str | None = None):
        """Initialize the Phabricator client.

        Args:
            token: API token. If None, reads from PHABRICATOR_TOKEN env var.
            host: Phabricator instance URL. If None, reads from PHABRICATOR_URL env var.
        """
        if token is None:
            token = os.getenv("PHABRICATOR_TOKEN")
        if not token:
            raise ValueError("PHABRICATOR_TOKEN environment variable is required")

        if host is None:
            host = os.getenv("PHABRICATOR_URL", "https://phabricator.wikimedia.org/api/")

        try:
            self.phab = create_phabricator_client(host=host, token=token)
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to initialize Phabricator client: {str(e)}") from e

    async def get_task(self, task_id: str) -> dict:
        """Get detailed information about a specific task.

        Args:
            task_id: Task ID (without 'T' prefix)

        Returns:
            Task data dictionary

        Raises:
            PhabricatorAPIError: If task not found or API error occurs
        """
        try:
            task = self.phab.maniphest.search(constraints={'ids': [int(task_id)]})
            if not task.data:
                raise PhabricatorAPIError(f"Task T{task_id} not found")
            return task.data[0]
        except ValueError as e:
            raise PhabricatorAPIError(f"Invalid task ID: {task_id}") from e
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to get task T{task_id}: {str(e)}") from e

    async def get_task_comments(self, task_id: str) -> list[dict]:
        """Get all comments on a task.

        Args:
            task_id: Task ID (without 'T' prefix)

        Returns:
            List of comment dictionaries
        """
        try:
            transactions = self.phab.maniphest.gettasktransactions(ids=[int(task_id)])
            # Handle different response formats
            if isinstance(transactions, dict) and task_id in transactions:
                task_transactions = transactions[task_id]
            elif isinstance(transactions, dict) and str(task_id) in transactions:
                task_transactions = transactions[str(task_id)]
            elif isinstance(transactions, list):
                task_transactions = transactions
            else:
                return []

            # Filter for comment-type transactions
            comments = []
            for t in task_transactions:
                if isinstance(t, dict) and t.get('type') == 'comment':
                    comments.append(t)

            return comments
        except Exception as e:
            # Return empty list if comments can't be retrieved rather than failing
            print(f"Warning: Could not get comments for task T{task_id}: {str(e)}")
            return []

    async def add_task_comment(self, task_id: str, comment: str) -> dict:
        """Add a comment to a task.

        Args:
            task_id: Task ID (without 'T' prefix)
            comment: Comment text to add

        Returns:
            Result dictionary from API
        """
        try:
            result = self.phab.maniphest.edit(
                transactions=[{"type": "comment", "value": comment}], objectIdentifier=f"T{task_id}"
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to add comment to task T{task_id}: {str(e)}") from e

    async def subscribe_to_task(self, task_id: str, user_phids: list[str]) -> dict:
        """Subscribe users to a task.

        Args:
            task_id: Task ID (without 'T' prefix)
            user_phids: List of user PHIDs to subscribe

        Returns:
            Result dictionary from API
        """
        try:
            result = self.phab.maniphest.edit(
                transactions=[{"type": "subscribers.add", "value": user_phids}],
                objectIdentifier=f"T{task_id}",
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to subscribe users to task T{task_id}: {str(e)}"
            ) from e

    async def get_differential_revision(self, revision_id: str) -> dict:
        """Get detailed information about a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)

        Returns:
            Revision data dictionary
        """
        try:
            revision = self.phab.differential.revision.search(
                constraints={'ids': [int(revision_id)]}
            )
            if not revision.data:
                raise PhabricatorAPIError(f"Revision D{revision_id} not found")
            return revision.data[0]
        except Exception:
            # Fallback to older API
            try:
                revisions = self.phab.differential.query(ids=[int(revision_id)])
                if not revisions:
                    raise PhabricatorAPIError(f"Revision D{revision_id} not found")
                return revisions[0]
            except Exception as e:
                raise PhabricatorAPIError(f"Failed to get revision D{revision_id}: {str(e)}") from e

    async def get_differential_comments(self, revision_id: str) -> list:
        """Get all comments and code review details for a differential revision."""
        try:
            # Try modern API with transactions attachment
            try:
                revision = self.phab.differential.revision.search(
                    constraints={'ids': [int(revision_id)]},
                    attachments={'transactions': True},
                )
                if revision.data and revision.data[0].get('attachments', {}).get('transactions'):
                    transactions = revision.data[0]['attachments']['transactions']['transactions']
                    return [
                        t
                        for t in transactions
                        if t.get('type')
                        in ('comment', 'inline', 'accept', 'reject', 'request-changes')
                    ]
            except Exception:
                pass

            # Fallback: try older differential API for comments
            try:
                comments_result = self.phab.differential.getrevisioncomments(ids=[int(revision_id)])
                if isinstance(comments_result, dict) and str(revision_id) in comments_result:
                    return comments_result[str(revision_id)]
                elif (
                    hasattr(comments_result, 'response')
                    and str(revision_id) in comments_result.response
                ):
                    return comments_result.response[str(revision_id)]
            except Exception:
                pass

            return []
        except Exception as e:
            print(f"Warning: Could not get comments for revision D{revision_id}: {str(e)}")
            return []

    async def get_differential_code_changes(self, revision_id: str) -> dict:
        """Get the actual code changes/diff for a differential revision."""
        try:
            # Get the diff details
            diffs = self.phab.differential.querydiffs(revisionIDs=[int(revision_id)])
            if not diffs:
                return {}

            # Get the latest diff
            latest_diff_id = max(diffs.keys(), key=lambda x: diffs[x]['dateCreated'])
            diff_data = diffs[latest_diff_id]

            # Get the changes
            changes = diff_data.get('changes', [])

            return {
                'diff_id': latest_diff_id,
                'changes': changes,
                'description': diff_data.get('description', ''),
                'date_created': diff_data.get('dateCreated'),
                'author': diff_data.get('authorName', 'Unknown'),
            }
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to get code changes for revision D{revision_id}: {str(e)}"
            ) from e

    async def add_differential_comment(self, revision_id: str, comment: str) -> dict:
        """Add a comment to a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            comment: Comment text to add

        Returns:
            Result dictionary from API
        """
        try:
            result = self.phab.differential.revision.edit(
                transactions=[{"type": "comment", "value": comment}],
                objectIdentifier=f"D{revision_id}",
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to add comment to revision D{revision_id}: {str(e)}"
            ) from e

    async def accept_differential_revision(self, revision_id: str) -> dict:
        """Accept a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)

        Returns:
            Result dictionary from API
        """
        try:
            result = self.phab.differential.revision.edit(
                transactions=[{"type": "accept", "value": True}], objectIdentifier=f"D{revision_id}"
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to accept revision D{revision_id}: {str(e)}") from e

    async def request_changes_differential_revision(
        self, revision_id: str, comment: str | None = None
    ) -> dict:
        """Request changes on a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            comment: Optional comment explaining the requested changes

        Returns:
            Result dictionary from API
        """
        try:
            transactions = [{"type": "reject", "value": True}]
            if comment:
                transactions.append({"type": "comment", "value": comment})

            result = self.phab.differential.revision.edit(
                transactions=transactions, objectIdentifier=f"D{revision_id}"
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to request changes for revision D{revision_id}: {str(e)}"
            ) from e

    async def subscribe_to_differential(self, revision_id: str, user_phids: list[str]) -> dict:
        """Subscribe users to a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            user_phids: List of user PHIDs to subscribe

        Returns:
            Result dictionary from API
        """
        try:
            result = self.phab.differential.revision.edit(
                transactions=[{"type": "subscribers.add", "value": user_phids}],
                objectIdentifier=f"D{revision_id}",
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to subscribe users to revision D{revision_id}: {str(e)}"
            ) from e

    async def get_revision_comments_with_context(
        self, revision_id: str, context_lines: int = 5
    ) -> dict[str, Any]:
        """Get all comments for a revision with surrounding code context.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            context_lines: Number of lines to include before/after inline comments

        Returns:
            Dictionary containing:
                - revision: Basic revision info
                - comments: All comments with enhanced inline comment data
                - code_changes: Full diff information
        """
        # Get basic revision info
        revision = await self.get_differential_revision(revision_id)

        # Get all comments
        comments = await self.get_differential_comments(revision_id)

        # Get code changes
        code_changes = await self.get_differential_code_changes(revision_id)

        # Enhance inline comments with code context
        enhanced_comments = []
        for comment in comments:
            if comment.get('type') == 'inline':
                enhanced_comment = await self._enhance_inline_comment(
                    comment, code_changes, context_lines
                )
                enhanced_comments.append(enhanced_comment)
            else:
                enhanced_comments.append(comment)

        return {'revision': revision, 'comments': enhanced_comments, 'code_changes': code_changes}

    async def _enhance_inline_comment(
        self, comment: dict[str, Any], code_changes: dict[str, Any], context_lines: int
    ) -> dict[str, Any]:
        """Enhance an inline comment with code context.

        Args:
            comment: The inline comment data
            code_changes: The diff data from get_differential_code_changes
            context_lines: Number of context lines

        Returns:
            Enhanced comment with code_context field
        """
        enhanced = comment.copy()

        # Extract file and line info from comment
        file_path = None
        line_number = None

        # Try different possible field locations
        if 'fields' in comment:
            fields = comment['fields']
            file_path = fields.get('path', fields.get('file'))
            line_number = fields.get('line', fields.get('lineNumber'))

        # Also check direct fields
        if not file_path:
            file_path = comment.get('path', comment.get('file'))
        if not line_number:
            line_number = comment.get('line', comment.get('lineNumber'))

        # If we have file and line info, find the code context
        if file_path and line_number and code_changes.get('changes'):
            code_context = self._extract_code_context(
                file_path, line_number, code_changes['changes'], context_lines
            )
            enhanced['code_context'] = code_context
            enhanced['enhanced_file'] = file_path
            enhanced['enhanced_line'] = line_number

        return enhanced

    def _extract_code_context(
        self, file_path: str, line_number: int, changes: list[dict], context_lines: int
    ) -> dict[str, Any] | None:
        """Extract code context around a specific line.

        Args:
            file_path: Path of the file
            line_number: Line number in the file
            changes: List of file changes from the diff
            context_lines: Number of context lines

        Returns:
            Dictionary with code context or None if not found
        """
        # Find the matching file in changes
        for change in changes:
            current_path = change.get('currentPath', change.get('newPath'))
            if current_path == file_path:
                # Found the file, now extract context from hunks
                hunks = change.get('hunks', [])

                for hunk in hunks:
                    new_offset = hunk.get('newOffset', 0)
                    new_length = hunk.get('newLength', 0)

                    # Check if the line falls within this hunk
                    if new_offset <= line_number < new_offset + new_length:
                        corpus = hunk.get('corpus', '')
                        lines = corpus.split('\n')

                        # Calculate relative position in hunk
                        hunk_line_idx = line_number - new_offset

                        # Extract context
                        start_idx = max(0, hunk_line_idx - context_lines)
                        end_idx = min(len(lines), hunk_line_idx + context_lines + 1)

                        context_lines_list = []
                        for i in range(start_idx, end_idx):
                            if i < len(lines):
                                line_num = new_offset + i
                                is_target = i == hunk_line_idx
                                context_lines_list.append(
                                    {
                                        'line_number': line_num,
                                        'content': lines[i],
                                        'is_target': is_target,
                                    }
                                )

                        return {
                            'file': file_path,
                            'target_line': line_number,
                            'hunk_info': f"@@ -{hunk.get('oldOffset')},{hunk.get('oldLength')} +{new_offset},{new_length} @@",
                            'lines': context_lines_list,
                        }

        return None

    async def add_inline_comment(
        self,
        revision_id: str,
        file_path: str,
        line_number: int,
        content: str,
        is_new_file: bool = True,
    ) -> dict:
        """Add an inline comment to a specific line in a differential revision.

        Args:
            revision_id: Revision ID (without 'D' prefix)
            file_path: Path to the file
            line_number: Line number to comment on
            content: Comment text
            is_new_file: Whether to comment on the new version (True) or old version (False)

        Returns:
            Result dictionary from API
        """
        try:
            # First get the differential to find the diff ID
            revision = await self.get_differential_revision(revision_id)

            # Try to get the current diff ID from the revision
            if 'fields' in revision and 'diffPHID' in revision['fields']:
                # For now, we'll try to create the inline comment with revision info
                pass

            # Use differential.createinline to create the inline comment
            result = self.phab.differential.createinline(
                revisionID=int(revision_id),
                content=content,
                filePath=file_path,
                lineNumber=int(line_number),
                isNewFile=is_new_file,
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to add inline comment to revision D{revision_id}: {str(e)}"
            ) from e

    async def reply_to_comment(self, comment_phid: str, content: str) -> dict:
        """Reply to an existing comment thread.

        Args:
            comment_phid: PHID of the comment to reply to
            content: Reply content

        Returns:
            Result dictionary from API
        """
        try:
            # This would require finding the parent object and adding a reply
            # The exact implementation depends on Phabricator version
            raise NotImplementedError(
                "Reply functionality requires specific Phabricator API endpoints"
            )
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to reply to comment: {str(e)}") from e

    async def mark_inline_comment_done(self, comment_phid: str) -> dict:
        """Mark an inline comment as done/resolved.

        Args:
            comment_phid: PHID of the inline comment

        Returns:
            Result dictionary from API
        """
        try:
            # This typically requires a specific transaction type
            # The exact implementation depends on Phabricator version
            raise NotImplementedError(
                "Mark done functionality requires specific Phabricator API endpoints"
            )
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to mark comment as done: {str(e)}") from e

    async def get_review_feedback_with_code_context(
        self, revision_id: str, context_lines: int = 7
    ) -> dict[str, Any]:
        """Get review feedback with intelligent code context for addressing comments.

        This method helps address code review comments by:
        1. Getting all review comments
        2. Correlating them with specific code locations using content analysis
        3. Providing rich context around commented code areas
        4. Formatting for easy understanding and action

        Args:
            revision_id: Revision ID (without 'D' prefix)
            context_lines: Number of lines to show around relevant code areas

        Returns:
            Dictionary containing:
                - revision: Basic revision info
                - review_feedback: List of feedback items with code context
                - summary: Summary of what needs to be addressed
        """
        try:
            # Get basic revision info
            revision = await self.get_differential_revision(revision_id)

            # Get all comments
            comments = await self.get_differential_comments(revision_id)

            # Get code changes
            code_changes = await self.get_differential_code_changes(revision_id)

            # Process comments and correlate with code
            review_feedback = []
            actionable_comments = []

            for comment in comments:
                content = comment.get('content', '')
                if content and content.strip():
                    actionable_comments.append(comment)

            # Correlate comments with code locations
            for comment in actionable_comments:
                feedback_item = await self._correlate_comment_with_code(
                    comment, code_changes, context_lines
                )
                if feedback_item:
                    review_feedback.append(feedback_item)

            # Generate summary
            summary = self._generate_review_summary(review_feedback)

            return {
                'revision': revision,
                'review_feedback': review_feedback,
                'summary': summary,
                'total_comments': len(actionable_comments),
                'comments_with_context': len([f for f in review_feedback if f.get('code_context')]),
            }

        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to get review feedback for D{revision_id}: {str(e)}"
            ) from e

    async def _correlate_comment_with_code(
        self, comment: dict[str, Any], code_changes: dict[str, Any], context_lines: int
    ) -> dict[str, Any] | None:
        """Correlate a comment with relevant code locations using content analysis."""
        content = comment.get('content', '').strip()
        if not content:
            return None

        feedback_item = {
            'comment': content,
            'author': comment.get('authorPHID', 'unknown'),
            'date': comment.get('dateCreated', ''),
            'type': 'general',  # Default type
            'code_context': None,
            'suggested_locations': [],
        }

        if not code_changes.get('changes'):
            return feedback_item

        # Extract keywords from comment that might indicate code locations
        keywords = self._extract_code_keywords_from_comment(content)

        # Search for relevant code locations
        relevant_locations = []
        for change in code_changes['changes']:
            file_path = change.get('currentPath', change.get('newPath', ''))
            hunks = change.get('hunks', [])

            for hunk in hunks:
                corpus = hunk.get('corpus', '')
                if not corpus:
                    continue

                lines = corpus.split('\n')
                new_offset = int(hunk.get('newOffset', 0))

                # Look for lines that match comment keywords
                for line_idx, line in enumerate(lines):
                    line_num = new_offset + line_idx
                    line_content = line[1:] if line.startswith(('+', '-', ' ')) else line

                    # Check if this line is relevant to the comment
                    relevance_score = self._calculate_line_relevance(
                        line_content, keywords, content
                    )

                    if relevance_score > 0:
                        # Get context around this line
                        context = self._get_code_context_around_line(
                            lines, line_idx, new_offset, context_lines, file_path, hunk
                        )

                        relevant_locations.append(
                            {
                                'file': file_path,
                                'line': line_num,
                                'relevance_score': relevance_score,
                                'context': context,
                                'line_content': line_content.strip(),
                            }
                        )

        # Sort by relevance and take the most relevant locations
        relevant_locations.sort(key=lambda x: x['relevance_score'], reverse=True)

        if relevant_locations:
            # Use the most relevant location as primary context
            best_location = relevant_locations[0]
            feedback_item['code_context'] = best_location['context']
            feedback_item['primary_file'] = best_location['file']
            feedback_item['primary_line'] = best_location['line']
            feedback_item['type'] = 'inline'  # Has code context

            # Include other relevant locations as suggestions
            feedback_item['suggested_locations'] = relevant_locations[
                1:3
            ]  # Top 2 additional locations

        return feedback_item

    def _extract_code_keywords_from_comment(self, comment: str) -> list[str]:
        """Extract potential code-related keywords from a comment."""

        keywords = []

        # Look for variable names (commonly referenced in code reviews)
        # Pattern: words that look like variable names
        var_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        potential_vars = re.findall(var_pattern, comment)

        # Filter for likely variable names (avoid common English words)
        common_words = {
            'the',
            'a',
            'an',
            'and',
            'or',
            'but',
            'in',
            'on',
            'at',
            'to',
            'for',
            'of',
            'with',
            'by',
            'is',
            'are',
            'was',
            'were',
            'be',
            'been',
            'have',
            'has',
            'had',
            'do',
            'does',
            'did',
            'will',
            'would',
            'could',
            'should',
            'may',
            'might',
            'can',
            'must',
            'this',
            'that',
            'these',
            'those',
            'not',
            'more',
            'less',
            'better',
            'best',
            'good',
            'bad',
            'nit',
            'comment',
            'code',
            'line',
            'function',
            'method',
            'class',
            'file',
        }

        for word in potential_vars:
            if (
                len(word) > 2
                and word.lower() not in common_words
                and not word.isupper()  # Skip ALL_CAPS (constants are less likely to be in comments)
                and ('_' in word or any(c.isupper() for c in word[1:]))
            ):  # snake_case or camelCase
                keywords.append(word)

        # Look for quoted strings (often variable names or values)
        quoted_pattern = r'["`\'](.*?)["`\']'
        quoted_items = re.findall(quoted_pattern, comment)
        keywords.extend(quoted_items)

        # Look for function calls
        func_pattern = r'(\w+)\s*\('
        functions = re.findall(func_pattern, comment)
        keywords.extend(functions)

        return list(set(keywords))  # Remove duplicates

    def _calculate_line_relevance(
        self, line_content: str, keywords: list[str], comment: str
    ) -> float:
        """Calculate how relevant a line of code is to a comment."""
        relevance_score = 0.0

        if not line_content.strip():
            return 0.0

        # Score based on keyword matches
        for keyword in keywords:
            if keyword in line_content:
                relevance_score += 2.0  # High score for exact keyword match
            elif keyword.lower() in line_content.lower():
                relevance_score += 1.0  # Medium score for case-insensitive match

        # Boost score for certain patterns mentioned in comments
        if 'result' in comment.lower() and 'result' in line_content.lower():
            relevance_score += 1.5

        if 'variable' in comment.lower() and '=' in line_content:
            relevance_score += 1.0

        if 'assignment' in comment.lower() and '=' in line_content:
            relevance_score += 1.0

        if 'unnecessary' in comment.lower() and line_content.strip().startswith(('+', '-')):
            relevance_score += 0.5

        # Reduce score for comment lines or empty lines
        if line_content.strip().startswith('#') or line_content.strip().startswith('//'):
            relevance_score *= 0.1

        return relevance_score

    def _get_code_context_around_line(
        self,
        lines: list[str],
        target_line_idx: int,
        offset: int,
        context_lines: int,
        file_path: str,
        hunk: dict,
    ) -> dict[str, Any]:
        """Get code context around a specific line."""
        start_idx = max(0, target_line_idx - context_lines)
        end_idx = min(len(lines), target_line_idx + context_lines + 1)

        context_lines_list = []
        for i in range(start_idx, end_idx):
            if i < len(lines):
                line_num = offset + i
                line_content = lines[i]

                # Determine line type
                line_type = 'context'
                if line_content.startswith('+'):
                    line_type = 'added'
                elif line_content.startswith('-'):
                    line_type = 'removed'

                # Clean content (remove diff markers)
                clean_content = (
                    line_content[1:] if line_content.startswith(('+', '-', ' ')) else line_content
                )

                context_lines_list.append(
                    {
                        'line_number': line_num,
                        'content': clean_content,
                        'raw_content': line_content,
                        'type': line_type,
                        'is_target': i == target_line_idx,
                        'is_highlighted': i == target_line_idx,
                    }
                )

        return {
            'file': file_path,
            'hunk_info': f"@@ -{hunk.get('oldOffset', 0)},{hunk.get('oldLength', 0)} +{offset},{hunk.get('newLength', 0)} @@",
            'lines': context_lines_list,
            'target_line': offset + target_line_idx,
        }

    def _generate_review_summary(self, review_feedback: list[dict[str, Any]]) -> str:
        """Generate a summary of review feedback to address."""
        if not review_feedback:
            return "No actionable review feedback found."

        total_feedback = len(review_feedback)
        inline_feedback = len([f for f in review_feedback if f.get('code_context')])
        general_feedback = total_feedback - inline_feedback

        summary_parts = [
            f"📋 Review Summary: {total_feedback} items to address",
            f"   • {inline_feedback} comments with specific code locations",
            f"   • {general_feedback} general comments",
        ]

        # Categorize feedback types
        categories = {}
        for feedback in review_feedback:
            content = feedback['comment'].lower()
            if 'nit' in content:
                categories['nits'] = categories.get('nits', 0) + 1
            elif any(word in content for word in ['error', 'bug', 'issue', 'problem']):
                categories['issues'] = categories.get('issues', 0) + 1
            elif any(word in content for word in ['suggest', 'recommend', 'consider']):
                categories['suggestions'] = categories.get('suggestions', 0) + 1
            else:
                categories['other'] = categories.get('other', 0) + 1

        if categories:
            summary_parts.append("\n📊 Feedback breakdown:")
            for category, count in categories.items():
                summary_parts.append(f"   • {count} {category}")

        return "\n".join(summary_parts)
