"""
byceps.services.attendance.attendance_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence

from sqlalchemy import select

from byceps.database import db, paginate, Pagination
from byceps.services.seating.dbmodels.seat import DbSeat
from byceps.services.ticketing.dbmodels.category import DbTicketCategory
from byceps.services.ticketing.dbmodels.ticket import DbTicket
from byceps.services.user.dbmodels.user import DbUser
from byceps.typing import PartyID, UserID

from .models import Attendee, AttendeeTicket


def get_attendees_paginated(
    party_id: PartyID,
    page: int,
    per_page: int,
    *,
    search_term: str | None = None,
) -> Pagination:
    """Return the party's ticket users with tickets and seats."""
    users_paginated = _get_users_paginated(
        party_id, page, per_page, search_term=search_term
    )
    db_users = users_paginated.items
    user_ids = {db_user.id for db_user in db_users}

    db_tickets = _get_tickets_for_users(party_id, user_ids)
    tickets_by_user_id = _index_tickets_by_user_id(db_tickets)

    attendees = list(_generate_attendees(db_users, tickets_by_user_id))

    users_paginated.items = attendees
    return users_paginated


def _get_users_paginated(
    party_id: PartyID,
    page: int,
    per_page: int,
    *,
    search_term: str | None = None,
) -> Pagination:
    # Drop revoked tickets here already to avoid users without tickets
    # being included in the list.

    stmt = (
        select(
            DbUser, db.func.lower(DbUser.screen_name).label('screen_name_lower')
        )
        .distinct()
        .options(
            db.load_only(DbUser.id, DbUser.screen_name, DbUser.deleted),
            db.joinedload(DbUser.avatar),
        )
        .join(DbTicket, DbTicket.used_by_id == DbUser.id)
        .filter(DbTicket.revoked == False)  # noqa: E712
        .join(DbTicketCategory)
        .filter(DbTicketCategory.party_id == party_id)
        .order_by('screen_name_lower')
    )

    if search_term:
        stmt = stmt.filter(DbUser.screen_name.ilike(f'%{search_term}%'))

    return paginate(stmt, page, per_page)


def _get_tickets_for_users(
    party_id: PartyID, user_ids: set[UserID]
) -> Sequence[DbTicket]:
    return (
        db.session.scalars(
            select(DbTicket)
            .options(
                db.joinedload(DbTicket.category),
                db.joinedload(DbTicket.occupied_seat).joinedload(DbSeat.area),
            )
            .filter(DbTicket.party_id == party_id)
            .filter(DbTicket.used_by_id.in_(user_ids))
            .filter(DbTicket.revoked == False)  # noqa: E712
        )
        .unique()
        .all()
    )


def _index_tickets_by_user_id(
    db_tickets: Iterable[DbTicket],
) -> dict[UserID, set[DbTicket]]:
    tickets_by_user_id = defaultdict(set)
    for db_ticket in db_tickets:
        tickets_by_user_id[db_ticket.used_by_id].add(db_ticket)
    return tickets_by_user_id


def _generate_attendees(
    db_users: Iterable[DbUser], tickets_by_user_id: dict[UserID, set[DbTicket]]
) -> Iterable[Attendee]:
    for db_user in db_users:
        db_tickets = tickets_by_user_id[db_user.id]
        attendee_tickets = _to_attendee_tickets(db_tickets)

        yield Attendee(
            user=db_user,
            tickets=attendee_tickets,
        )


def _to_attendee_tickets(
    db_tickets: Iterable[DbTicket],
) -> list[AttendeeTicket]:
    attendee_tickets = [
        _to_attendee_ticket(db_ticket) for db_ticket in db_tickets
    ]
    attendee_tickets.sort(key=_get_attendee_ticket_sort_key)
    return attendee_tickets


def _to_attendee_ticket(db_ticket: DbTicket) -> AttendeeTicket:
    return AttendeeTicket(
        seat=db_ticket.occupied_seat,
        checked_in=db_ticket.user_checked_in,
    )


def _get_attendee_ticket_sort_key(
    attendee_ticket: AttendeeTicket,
) -> tuple[bool, str, bool]:
    return (
        # List tickets with occupied seat first.
        attendee_ticket.seat is None,

        # Sort by seat label.
        attendee_ticket.seat.label if attendee_ticket.seat else None,

        # List checked in tickets first.
        not attendee_ticket.checked_in,
    )
