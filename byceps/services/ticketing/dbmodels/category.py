"""
byceps.services.ticketing.dbmodels.category
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.database import db, generate_uuid4
from byceps.typing import PartyID
from byceps.util.instances import ReprBuilder


class DbTicketCategory(db.Model):
    """A ticket category."""

    __tablename__ = 'ticket_categories'
    __table_args__ = (db.UniqueConstraint('party_id', 'title'),)

    id = db.Column(db.Uuid, default=generate_uuid4, primary_key=True)
    party_id = db.Column(
        db.UnicodeText, db.ForeignKey('parties.id'), index=True, nullable=False
    )
    title = db.Column(db.UnicodeText, nullable=False)

    def __init__(self, party_id: PartyID, title: str) -> None:
        self.party_id = party_id
        self.title = title

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add('id', str(self.id))
            .add('party', self.party_id)
            .add_with_lookup('title')
            .build()
        )
