"""
byceps.services.authentication.api.dbmodels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.mutable import MutableList

from byceps.database import db, generate_uuid4
from byceps.services.authorization.models import PermissionID
from byceps.typing import UserID


class DbApiToken(db.Model):
    """An authentication and authorization token for API clients."""

    __tablename__ = 'api_tokens'

    id = db.Column(db.Uuid, default=generate_uuid4, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    creator_id = db.Column(db.Uuid, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.UnicodeText, nullable=False)
    permissions = db.Column(MutableList.as_mutable(db.JSONB), nullable=False)
    description = db.Column(db.UnicodeText, nullable=True)
    suspended = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(
        self,
        creator_id: UserID,
        token: str,
        permissions: set[PermissionID],
        *,
        description: str | None,
    ) -> None:
        self.creator_id = creator_id
        self.token = token
        self.permissions = list(permissions)
        self.description = description
