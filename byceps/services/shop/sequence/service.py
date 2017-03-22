"""
byceps.services.shop.sequence.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from ....database import db

from .models import PartySequence, Purpose


def create_party_sequence(party_id, purpose, prefix):
    """Create a sequence for that party and purpose."""
    sequence = PartySequence(party_id, purpose, prefix)
    db.session.add(sequence)
    db.session.commit()


class NumberGenerationFailed(Exception):
    """Indicate that generating a prefixed, sequential number has failed."""

    def __init__(self, message):
        self.message = message


def generate_article_number(party_id):
    """Generate and reserve an unused, unique article number for this party."""
    prefix = get_article_number_prefix(party_id)

    if prefix is None:
        raise NumberGenerationFailed(
            'No article number prefix is configured for party "{}".'
            .format(party_id))

    article_sequence_number = _get_next_sequence_number(party_id,
        Purpose.article)

    return '{}{:05d}'.format(prefix, article_sequence_number)


def generate_order_number(party_id):
    """Generate and reserve an unused, unique order number for this party."""
    prefix = get_order_number_prefix(party_id)

    if prefix is None:
        raise NumberGenerationFailed(
            'No order number prefix is configured for party "{}".'
            .format(party_id))

    order_sequence_number = _get_next_sequence_number(party_id, Purpose.order)

    return '{}{:05d}'.format(prefix, order_sequence_number)


def _get_next_sequence_number(party_id, purpose):
    """Calculate and reserve the next sequence number for the party and
    purpose.
    """
    sequence = PartySequence.query \
        .filter_by(party_id=party_id) \
        .filter_by(_purpose=purpose.name) \
        .with_for_update() \
        .one_or_none()

    if sequence is None:
        raise NumberGenerationFailed(
            'No sequence configured for party "{}" and purpose "{}".'
            .format(party_id, purpose.name))

    sequence.value = PartySequence.value + 1
    db.session.commit()
    return sequence.value


def get_article_number_prefix(party_id):
    """Return the article number prefix for that party, or `None` if
    none is defined.
    """
    return _find_prefix_attr(party_id, Purpose.article)


def get_order_number_prefix(party_id):
    """Return the order number prefix for that party, or `None` if
    none is defined.
    """
    return _find_prefix_attr(party_id, Purpose.order)


def _find_prefix_attr(party_id, purpose):
    sequence = PartySequence.query.get((party_id, purpose.name))
    return getattr(sequence, 'prefix', None)
