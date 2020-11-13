"""
byceps.services.authentication.session.models.recent_login
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from .....database import db
from .....typing import UserID


class RecentLogin(db.Model):
    """A user's most recent successful login."""

    __tablename__ = 'authn_recent_logins'

    user_id = db.Column(db.Uuid, db.ForeignKey('users.id'), primary_key=True)
    occurred_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id: UserID, occurred_at: datetime) -> None:
        self.user_id = user_id
        self.occurred_at = occurred_at
