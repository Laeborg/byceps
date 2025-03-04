"""
byceps.services.news.news_item_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from collections.abc import Sequence
import dataclasses
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.sql import Select
import structlog

from byceps.database import db, paginate, Pagination
from byceps.events.news import NewsItemPublishedEvent
from byceps.services.site import site_service
from byceps.services.site.models import SiteID
from byceps.services.user import user_service
from byceps.services.user.models.user import User
from byceps.typing import UserID
from byceps.util.iterables import find
from byceps.util.result import Ok, Result

from . import news_channel_service, news_html_service, news_image_service
from .dbmodels.channel import DbNewsChannel
from .dbmodels.item import (
    DbCurrentNewsItemVersionAssociation,
    DbNewsItem,
    DbNewsItemVersion,
)
from .models import (
    AdminListNewsItem,
    BodyFormat,
    NewsChannelID,
    NewsHeadline,
    NewsImage,
    NewsImageID,
    NewsItem,
    NewsItemID,
    NewsItemVersionID,
    RenderedNewsItem,
)


log = structlog.get_logger()


def create_item(
    channel_id: NewsChannelID,
    slug: str,
    creator_id: UserID,
    title: str,
    body: str,
    body_format: BodyFormat,
    *,
    image_url_path: str | None = None,
) -> NewsItem:
    """Create a news item, a version, and set the version as the item's
    current one.
    """
    db_item = DbNewsItem(channel_id, slug)
    db.session.add(db_item)

    db_version = _create_version(
        db_item,
        creator_id,
        title,
        body,
        body_format,
        image_url_path=image_url_path,
    )
    db.session.add(db_version)

    db_current_version_association = DbCurrentNewsItemVersionAssociation(
        db_item, db_version
    )
    db.session.add(db_current_version_association)

    db.session.commit()

    return _db_entity_to_item(db_item)


def update_item(
    item_id: NewsItemID,
    slug: str,
    creator_id: UserID,
    title: str,
    body: str,
    body_format: BodyFormat,
    *,
    image_url_path: str | None = None,
) -> NewsItem:
    """Update a news item by creating a new version of it and setting
    the new version as the current one.
    """
    db_item = _get_db_item(item_id)

    db_item.slug = slug

    db_version = _create_version(
        db_item,
        creator_id,
        title,
        body,
        body_format,
        image_url_path=image_url_path,
    )
    db.session.add(db_version)

    db_item.current_version = db_version

    db.session.commit()

    return _db_entity_to_item(db_item)


def _create_version(
    db_item: DbNewsItem,
    creator_id: UserID,
    title: str,
    body: str,
    body_format: BodyFormat,
    *,
    image_url_path: str | None = None,
) -> DbNewsItemVersion:
    db_version = DbNewsItemVersion(
        db_item, creator_id, title, body, body_format
    )

    if image_url_path:
        db_version.image_url_path = image_url_path

    return db_version


def set_featured_image(item_id: NewsItemID, image_id: NewsImageID) -> None:
    """Set an image as featured image."""
    db_item = _get_db_item(item_id)

    db_item.featured_image_id = image_id
    db.session.commit()


def publish_item(
    item_id: NewsItemID,
    *,
    publish_at: datetime | None = None,
    initiator_id: UserID | None = None,
) -> NewsItemPublishedEvent:
    """Publish a news item."""
    db_item = _get_db_item(item_id)

    if db_item.published:
        raise ValueError('News item has already been published')

    now = datetime.utcnow()
    if publish_at is None:
        publish_at = now

    initiator: User | None
    if initiator_id is not None:
        initiator = user_service.get_user(initiator_id)
    else:
        initiator = None

    db_item.published_at = publish_at
    db.session.commit()

    item = _db_entity_to_item(db_item)

    if item.channel.announcement_site_id is not None:
        site = site_service.get_site(SiteID(item.channel.announcement_site_id))
        external_url = f'https://{site.server_name}/news/{item.slug}'
    else:
        external_url = None

    return NewsItemPublishedEvent(
        occurred_at=now,
        initiator_id=initiator.id if initiator else None,
        initiator_screen_name=initiator.screen_name if initiator else None,
        item_id=item.id,
        channel_id=item.channel.id,
        published_at=publish_at,
        title=item.title,
        external_url=external_url,
    )


def unpublish_item(
    item_id: NewsItemID,
    *,
    initiator_id: UserID | None = None,
) -> None:
    """Unublish a news item."""
    db_item = _get_db_item(item_id)

    if not db_item.published:
        raise ValueError('News item is not published')

    db_item.published_at = None
    db.session.commit()


def delete_item(item_id: NewsItemID) -> None:
    """Delete a news item and its versions."""
    db.session.execute(
        delete(DbCurrentNewsItemVersionAssociation).where(
            DbCurrentNewsItemVersionAssociation.item_id == item_id
        )
    )
    db.session.execute(
        delete(DbNewsItemVersion).where(DbNewsItemVersion.item_id == item_id)
    )
    db.session.execute(delete(DbNewsItem).where(DbNewsItem.id == item_id))
    db.session.commit()


def find_item(item_id: NewsItemID) -> NewsItem | None:
    """Return the item with that id, or `None` if not found."""
    db_item = _find_db_item(item_id)

    if db_item is None:
        return None

    return _db_entity_to_item(db_item)


def _find_db_item(item_id: NewsItemID) -> DbNewsItem | None:
    """Return the item with that id, or `None` if not found."""
    return (
        db.session.scalars(
            select(DbNewsItem)
            .filter(DbNewsItem.id == item_id)
            .options(
                db.joinedload(DbNewsItem.channel),
                db.joinedload(DbNewsItem.images),
            )
        )
        .unique()
        .one_or_none()
    )


def _get_db_item(item_id: NewsItemID) -> DbNewsItem:
    """Return the item with that id, or raise an exception."""
    db_item = _find_db_item(item_id)

    if db_item is None:
        raise ValueError(f'Unknown news item ID "{item_id}".')

    return db_item


def find_rendered_item_by_slug(
    channel_ids: set[NewsChannelID], slug: str, *, published_only: bool = False
) -> RenderedNewsItem | None:
    """Return the rendered item identified by that slug in one of the
    given channels, or `None` if not found.
    """
    stmt = (
        select(DbNewsItem)
        .filter(DbNewsItem.channel_id.in_(channel_ids))
        .filter_by(slug=slug)
        .options(
            db.joinedload(DbNewsItem.channel),
            db.joinedload(DbNewsItem.current_version_association).joinedload(
                DbCurrentNewsItemVersionAssociation.version
            ),
            db.joinedload(DbNewsItem.images),
        )
    )

    if published_only:
        stmt = stmt.filter(DbNewsItem.published_at <= datetime.utcnow())

    db_item = db.session.scalars(stmt).unique().one_or_none()

    if db_item is None:
        return None

    item = _db_entity_to_item(db_item)
    return render_html(item)


def get_rendered_items_paginated(
    channel_ids: set[NewsChannelID],
    page: int,
    items_per_page: int,
    *,
    published_only: bool = False,
) -> Pagination:
    """Return the rendered news items to show on the specified page."""
    stmt = _get_items_stmt(channel_ids)

    if published_only:
        now = datetime.utcnow()
        stmt = stmt.filter(DbNewsItem.published_at <= now)

    def item_mapper(db_item: DbNewsItem) -> RenderedNewsItem:
        item = _db_entity_to_item(db_item)
        return render_html(item)

    return paginate(stmt, page, items_per_page, item_mapper=item_mapper)


def get_admin_list_items_paginated(
    channel_ids: set[NewsChannelID], page: int, items_per_page: int
) -> Pagination:
    """Return the news items to show on the specified page."""
    stmt = _get_items_stmt(channel_ids)

    def to_admin_list_item(db_item: DbNewsItem) -> AdminListNewsItem:
        db_version = db_item.current_version

        return AdminListNewsItem(
            id=db_item.id,
            created_at=db_version.created_at,
            creator=db_version.creator_id,
            slug=db_item.slug,
            title=db_version.title,
            image_url_path=db_version.image_url_path,
            image_total=len(db_item.images),
            published=db_item.published,
        )

    pagination = paginate(
        stmt, page, items_per_page, item_mapper=to_admin_list_item
    )

    user_ids = {item.creator for item in pagination.items}
    users = user_service.get_users(user_ids, include_avatars=True)
    users_by_id = user_service.index_users_by_id(users)
    pagination.items = [
        dataclasses.replace(item, creator=users_by_id[item.creator])
        for item in pagination.items
    ]

    return pagination


def get_headlines_paginated(
    channel_ids: set[NewsChannelID],
    page: int,
    items_per_page: int,
    *,
    published_only: bool = False,
) -> Pagination:
    """Return the headlines to show on the specified page."""
    stmt = (
        select(DbNewsItem)
        .filter(DbNewsItem.channel_id.in_(channel_ids))
        .options(
            db.joinedload(DbNewsItem.current_version_association).joinedload(
                DbCurrentNewsItemVersionAssociation.version
            )
        )
        .order_by(DbNewsItem.published_at.desc())
    )

    if published_only:
        now = datetime.utcnow()
        stmt = stmt.filter(DbNewsItem.published_at <= now)

    return paginate(
        stmt, page, items_per_page, item_mapper=_db_entity_to_headline
    )


def get_recent_headlines(
    channel_ids: frozenset[NewsChannelID] | set[NewsChannelID], limit: int
) -> list[NewsHeadline]:
    """Return the most recent headlines."""
    db_items = (
        db.session.scalars(
            select(DbNewsItem)
            .filter(DbNewsItem.channel_id.in_(channel_ids))
            .options(
                db.joinedload(
                    DbNewsItem.current_version_association
                ).joinedload(DbCurrentNewsItemVersionAssociation.version)
            )
            .filter(DbNewsItem.published_at <= datetime.utcnow())
            .order_by(DbNewsItem.published_at.desc())
            .limit(limit)
        )
        .unique()
        .all()
    )

    return [_db_entity_to_headline(db_item) for db_item in db_items]


def _get_items_stmt(channel_ids: set[NewsChannelID]) -> Select:
    return (
        select(DbNewsItem)
        .filter(DbNewsItem.channel_id.in_(channel_ids))
        .options(
            db.joinedload(DbNewsItem.channel),
            db.joinedload(DbNewsItem.current_version_association).joinedload(
                DbCurrentNewsItemVersionAssociation.version
            ),
            db.joinedload(DbNewsItem.images),
        )
        .order_by(DbNewsItem.published_at.desc())
    )


def get_item_versions(item_id: NewsItemID) -> Sequence[DbNewsItemVersion]:
    """Return all item versions, sorted from most recent to oldest."""
    return db.session.scalars(
        select(DbNewsItemVersion)
        .filter_by(item_id=item_id)
        .order_by(DbNewsItemVersion.created_at.desc())
    ).all()


def get_current_item_version(item_id: NewsItemID) -> DbNewsItemVersion:
    """Return the item's current version."""
    db_item = _get_db_item(item_id)

    return db_item.current_version


def find_item_version(
    version_id: NewsItemVersionID,
) -> DbNewsItemVersion | None:
    """Return the item version with that ID, or `None` if not found."""
    return db.session.get(DbNewsItemVersion, version_id)


def has_channel_items(channel_id: NewsChannelID) -> bool:
    """Return `True` if the channel contains items."""
    return db.session.scalar(
        select(
            select(DbNewsItem)
            .join(DbNewsChannel)
            .filter(DbNewsChannel.id == channel_id)
            .exists()
        )
    )


def get_item_count_by_channel_id() -> dict[NewsChannelID, int]:
    """Return news item count (including 0) per channel, indexed by
    channel ID.
    """
    channel_ids_and_item_counts = (
        db.session.execute(
            select(DbNewsChannel.id, db.func.count(DbNewsItem.id))
            .outerjoin(DbNewsItem)
            .group_by(DbNewsChannel.id)
        )
        .tuples()
        .all()
    )

    return dict(channel_ids_and_item_counts)


def _db_entity_to_item(db_item: DbNewsItem) -> NewsItem:
    channel = news_channel_service._db_entity_to_channel(db_item.channel)

    image_url_path = _assemble_image_url_path(db_item)
    images = [
        news_image_service._db_entity_to_image(image, channel.id)
        for image in db_item.images
    ]

    return NewsItem(
        id=db_item.id,
        channel=channel,
        slug=db_item.slug,
        published_at=db_item.published_at,
        published=db_item.published_at is not None,
        title=db_item.current_version.title,
        body=db_item.current_version.body,
        body_format=db_item.current_version.body_format,
        image_url_path=image_url_path,
        images=images,
        featured_image_id=db_item.featured_image_id,
    )


def _assemble_image_url_path(db_item: DbNewsItem) -> str | None:
    url_path = db_item.current_version.image_url_path

    if not url_path:
        return None

    return f'/data/global/news_channels/{db_item.channel_id}/{url_path}'


def render_html(item: NewsItem) -> RenderedNewsItem:
    """Render item's raw body and featured image to HTML."""
    return RenderedNewsItem(
        channel=item.channel,
        slug=item.slug,
        published_at=item.published_at,
        published=item.published,
        title=item.title,
        featured_image_html=_render_featured_image_html(item),
        body_html=_render_body_html(item),
        image_url_path=item.image_url_path,
    )


def _render_featured_image_html(item: NewsItem) -> Result[str | None, str]:
    featured_image = _find_featured_image(item)
    if not featured_image:
        return Ok(None)

    result = news_html_service.render_featured_image_html(featured_image)

    if result.is_err():
        # Log, but do not return error.
        log.warning(
            'HTML rendering of featured image for news item %s failed: %s',
            item.id,
            result.unwrap_err(),
        )

    return Ok(result.unwrap())


def _render_body_html(item: NewsItem) -> Result[str, str]:
    result = news_html_service.render_body_html(item)

    if result.is_err():
        # Log, but do not return error.
        log.warning(
            'HTML rendering of body for news item %s failed: %s',
            item.id,
            result.unwrap_err(),
        )

    return result


def _find_featured_image(item: NewsItem) -> NewsImage | None:
    if not item.featured_image_id:
        return None

    return find(item.images, lambda image: image.id == item.featured_image_id)


def _db_entity_to_headline(db_item: DbNewsItem) -> NewsHeadline:
    return NewsHeadline(
        slug=db_item.slug,
        published_at=db_item.published_at,
        published=db_item.published_at is not None,
        title=db_item.current_version.title,
    )
