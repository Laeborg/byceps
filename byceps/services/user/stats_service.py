"""
byceps.services.user.stats_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime, timedelta

from ...database import db

from .dbmodels.user import User as DbUser


def count_users() -> int:
    """Return the number of users."""
    return db.session \
        .query(DbUser) \
        .count()


def count_users_created_since(delta: timedelta) -> int:
    """Return the number of user accounts created since `delta` ago."""
    filter_starts_at = datetime.utcnow() - delta

    return db.session \
        .query(DbUser) \
        .filter(DbUser.created_at >= filter_starts_at) \
        .count()


def count_active_users() -> int:
    """Return the number of active user accounts.

    Uninitialized, suspended or deleted accounts are excluded.
    """
    return db.session \
        .query(DbUser) \
        .filter_by(initialized=True) \
        .filter_by(suspended=False) \
        .filter_by(deleted=False) \
        .count()


def count_uninitialized_users() -> int:
    """Return the number of uninitialized user accounts.

    Suspended or deleted accounts are excluded.
    """
    return db.session \
        .query(DbUser) \
        .filter_by(initialized=False) \
        .filter_by(suspended=False) \
        .filter_by(deleted=False) \
        .count()


def count_suspended_users() -> int:
    """Return the number of suspended user accounts."""
    return db.session \
        .query(DbUser) \
        .filter_by(suspended=True) \
        .filter_by(deleted=False) \
        .count()


def count_deleted_users() -> int:
    """Return the number of deleted user accounts."""
    return db.session \
        .query(DbUser) \
        .filter_by(deleted=True) \
        .count()
