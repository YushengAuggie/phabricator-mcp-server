"""Pydantic models for type safety and validation."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TaskInfo(BaseModel):
    """Model for Phabricator task information."""

    id: str
    title: str
    description: str
    status: str
    priority: str
    author_phid: Optional[str] = None
    assigned_phid: Optional[str] = None


class DifferentialInfo(BaseModel):
    """Model for Phabricator differential revision information."""

    id: str
    title: str
    summary: str
    status: str
    author_phid: str


class Comment(BaseModel):
    """Model for comments on tasks or differentials."""

    author_phid: str
    content: str
    date_created: Optional[str] = None


class TaskCommentInput(BaseModel):
    """Input model for adding task comments."""

    task_id: str = Field(..., description="Task ID (without 'T' prefix)")
    comment: str = Field(..., description="Comment text to add")


class DifferentialCommentInput(BaseModel):
    """Input model for adding differential comments."""

    revision_id: str = Field(..., description="Revision ID (without 'D' prefix)")
    comment: str = Field(..., description="Comment text to add")


class SubscriptionInput(BaseModel):
    """Input model for subscription operations."""

    user_phids: List[str] = Field(..., description="List of user PHIDs to subscribe")


class TaskSubscriptionInput(SubscriptionInput):
    """Input model for task subscription."""

    task_id: str = Field(..., description="Task ID (without 'T' prefix)")


class DifferentialSubscriptionInput(SubscriptionInput):
    """Input model for differential subscription."""

    revision_id: str = Field(..., description="Revision ID (without 'D' prefix)")
