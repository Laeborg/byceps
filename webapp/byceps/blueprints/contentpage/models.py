# -*- coding: utf-8 -*-

"""
byceps.blueprints.contentpage.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from datetime import datetime
from operator import attrgetter

from flask import g, url_for
from werkzeug.routing import BuildError

from ...database import BaseQuery, db, generate_uuid
from ...util.instances import ReprBuilder

from ..party.models import Party
from ..user.models import User


class ContentPageQuery(BaseQuery):

    def for_current_party(self):
        return self.for_party(g.party)

    def for_party(self, party):
        return self.for_party_with_id(party.id)

    def for_party_with_id(self, party_id):
        return self.filter_by(party_id=party_id)


class ContentPage(db.Model):
    """A content page."""
    __tablename__ = 'content_pages'
    __table_args__ = (
        db.UniqueConstraint('party_id', 'name'),
        db.UniqueConstraint('party_id', 'url_path'),
    )
    query_class = ContentPageQuery

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    party_id = db.Column(db.Unicode(20), db.ForeignKey('parties.id'))
    party = db.relationship(Party)
    name = db.Column(db.Unicode(40))
    url_path = db.Column(db.Unicode(40))

    def generate_url(self):
        try:
            return url_for('contentpage.{}'.format(self.name))
        except BuildError:
            return None

    def get_latest_version(self):
        """Return the most recent version.

        A page is excepted to have at least one version (the initial
        one).
        """
        return self.get_versions()[0]

    def get_versions(self):
        """Return all versions, sorted from most recent to oldest."""
        return list(
            sorted(self.versions, key=attrgetter('created_at'), reverse=True))

    def __repr__(self):
        return ReprBuilder(self) \
            .add_with_lookup('id') \
            .add('party', self.party_id) \
            .add_with_lookup('name') \
            .add_with_lookup('url_path') \
            .build()


class ContentPageVersion(db.Model):
    """A snapshot of a content page at a certain time."""
    __tablename__ = 'content_page_versions'

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    page_id = db.Column(db.Uuid, db.ForeignKey('content_pages.id'))
    page = db.relationship(ContentPage, backref='versions')
    created_at = db.Column(db.DateTime, default=datetime.now)
    creator_id = db.Column(db.Uuid, db.ForeignKey('users.id'))
    creator = db.relationship(User)
    title = db.Column(db.Unicode(80))
    body = db.Column(db.UnicodeText)

    def __repr__(self):
        return ReprBuilder(self) \
            .add_with_lookup('id') \
            .add_with_lookup('page') \
            .add_with_lookup('created_at') \
            .add_with_lookup('creator') \
            .add_with_lookup('title') \
            .add('body length', len(self.body)) \
            .build()
