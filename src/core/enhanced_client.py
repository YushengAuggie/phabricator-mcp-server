"""Enhanced Phabricator client with code context for comments."""

from typing import Any, Dict, List, Optional

from .client import PhabricatorAPIError, PhabricatorClient


class EnhancedPhabricatorClient(PhabricatorClient):
    """Extended client with enhanced comment retrieval capabilities."""

    async def get_revision_comments_with_context(
        self, revision_id: str, context_lines: int = 5
    ) -> Dict[str, Any]:
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
        self, comment: Dict[str, Any], code_changes: Dict[str, Any], context_lines: int
    ) -> Dict[str, Any]:
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
        # The exact field names depend on Phabricator version
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
        self, file_path: str, line_number: int, changes: List[Dict], context_lines: int
    ) -> Optional[Dict[str, Any]]:
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
    ) -> Dict:
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
            # Build the inline comment transaction
            # The exact format depends on your Phabricator version
            transactions = [
                {
                    "type": "inline",
                    "value": {
                        "content": content,
                        "path": file_path,
                        "line": line_number,
                        "isNewFile": is_new_file,
                    },
                }
            ]

            result = self.phab.differential.revision.edit(
                transactions=transactions, objectIdentifier=f"D{revision_id}"
            )
            return result
        except Exception as e:
            raise PhabricatorAPIError(
                f"Failed to add inline comment to revision D{revision_id}: {str(e)}"
            )

    async def reply_to_comment(self, comment_phid: str, content: str) -> Dict:
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
            raise PhabricatorAPIError(f"Failed to reply to comment: {str(e)}")

    async def mark_inline_comment_done(self, comment_phid: str) -> Dict:
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
            raise PhabricatorAPIError(f"Failed to mark comment as done: {str(e)}")

