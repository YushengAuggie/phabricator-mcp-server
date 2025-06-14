"""Enhanced Phabricator API client with proper error handling and type safety."""

import os
from typing import Dict, List, Optional

from phabricator import Phabricator


class PhabricatorAPIError(Exception):
    """Custom exception for Phabricator API errors."""

    pass


class PhabricatorClient:
    """Enhanced Phabricator API client with comprehensive functionality."""

    def __init__(self, token: Optional[str] = None, host: Optional[str] = None):
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
            self.phab = Phabricator(host=host, token=token)
            self.phab.update_interfaces()
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to initialize Phabricator client: {str(e)}")

    async def get_task(self, task_id: str) -> Dict:
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
        except ValueError:
            raise PhabricatorAPIError(f"Invalid task ID: {task_id}")
        except Exception as e:
            raise PhabricatorAPIError(f"Failed to get task T{task_id}: {str(e)}")

    async def get_task_comments(self, task_id: str) -> List[Dict]:
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

    async def add_task_comment(self, task_id: str, comment: str) -> Dict:
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
            raise PhabricatorAPIError(f"Failed to add comment to task T{task_id}: {str(e)}")

    async def subscribe_to_task(self, task_id: str, user_phids: List[str]) -> Dict:
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
            raise PhabricatorAPIError(f"Failed to subscribe users to task T{task_id}: {str(e)}")

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
                raise PhabricatorAPIError(f"Failed to get revision D{revision_id}: {str(e)}")

    async def get_differential_comments(self, revision_id: str) -> list:
        """Get all comments and code review details for a differential revision."""
        try:
            # Try to get transactions with the proper attachment
            try:
                revision = self.phab.differential.revision.search(
                    constraints={'ids': [int(revision_id)]},
                    attachments={'reviewers': True, 'reviewers-extra': True, 'transactions': True},
                )
                if revision.data and revision.data[0].get('attachments', {}).get('transactions'):
                    transactions = revision.data[0]['attachments']['transactions']['transactions']
                    comments = []
                    for t in transactions:
                        if t.get('type') in (
                            'comment',
                            'inline',
                            'accept',
                            'reject',
                            'request-changes',
                        ):
                            comments.append(t)
                    return comments
            except:
                pass

            # Fallback: try transaction.search directly
            try:
                transactions = self.phab.transaction.search(objectIdentifier=f"D{revision_id}")
                if hasattr(transactions, 'data') and transactions.data:
                    comments = []
                    for t in transactions.data:
                        if t.get('type') in (
                            'comment',
                            'inline',
                            'accept',
                            'reject',
                            'request-changes',
                        ):
                            comments.append(t)
                    return comments
            except:
                pass

            # Fallback: try older comment API
            try:
                comments_result = self.phab.differential.getrevisioncomments(ids=[int(revision_id)])
                if (
                    hasattr(comments_result, 'response')
                    and str(revision_id) in comments_result.response
                ):
                    return comments_result.response[str(revision_id)]
                elif isinstance(comments_result, dict) and str(revision_id) in comments_result:
                    return comments_result[str(revision_id)]
            except:
                pass

            return []
        except Exception as e:
            print(f"Warning: Could not get comments for revision D{revision_id}: {str(e)}")
            return []

    async def get_differential_code_changes(self, revision_id: str) -> Dict:
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
            )

    async def add_differential_comment(self, revision_id: str, comment: str) -> Dict:
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
            raise PhabricatorAPIError(f"Failed to add comment to revision D{revision_id}: {str(e)}")

    async def accept_differential_revision(self, revision_id: str) -> Dict:
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
            raise PhabricatorAPIError(f"Failed to accept revision D{revision_id}: {str(e)}")

    async def request_changes_differential_revision(
        self, revision_id: str, comment: Optional[str] = None
    ) -> Dict:
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
            )

    async def subscribe_to_differential(self, revision_id: str, user_phids: List[str]) -> Dict:
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
            )
