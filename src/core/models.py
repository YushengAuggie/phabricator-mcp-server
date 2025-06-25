"""Pydantic models for type safety and validation."""

from pydantic import BaseModel


class TaskInfo(BaseModel):
    """Model for Phabricator task information."""

    id: str
    title: str
    description: str
    status: str
    priority: str
    author_phid: str | None = None
    assigned_phid: str | None = None


class DifferentialInfo(BaseModel):
    """Model for Phabricator differential revision information."""

    id: str
    title: str
    summary: str
    status: str
    author_phid: str
