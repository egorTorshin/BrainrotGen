"""ORM model registry — import every model so Base.metadata is complete"""

from brainrot_backend.models.user import User
from brainrot_backend.models.job import Job

__all__ = ["User", "Job"]
