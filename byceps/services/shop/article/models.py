"""
byceps.services.shop.article.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import NewType, Union
from uuid import UUID

from flask_babel import lazy_gettext
from moneyed import Money

from byceps.services.shop.shop.models import ShopID


ArticleID = NewType('ArticleID', UUID)


ArticleNumber = NewType('ArticleNumber', str)


ArticleNumberSequenceID = NewType('ArticleNumberSequenceID', UUID)


@dataclass(frozen=True)
class ArticleNumberSequence:
    id: ArticleNumberSequenceID
    shop_id: ShopID
    prefix: str
    value: int
    archived: bool


ArticleType = Enum(
    'ArticleType', ['physical', 'ticket', 'ticket_bundle', 'other']
)


_ARTICLE_TYPE_LABELS = {
    ArticleType.physical: lazy_gettext('physical'),
    ArticleType.ticket: lazy_gettext('Ticket'),
    ArticleType.ticket_bundle: lazy_gettext('Ticket bundle'),
    ArticleType.other: lazy_gettext('other'),
}


def get_article_type_label(article_type: ArticleType) -> str:
    """Return a label for the article type."""
    return _ARTICLE_TYPE_LABELS[article_type]


ArticleTypeParams = dict[str, Union[str, int]]


AttachedArticleID = NewType('AttachedArticleID', UUID)


@dataclass(frozen=True)
class Article:
    id: ArticleID
    shop_id: ShopID
    item_number: ArticleNumber
    type_: ArticleType
    type_params: ArticleTypeParams
    description: str
    price: Money
    tax_rate: Decimal
    available_from: datetime | None
    available_until: datetime | None
    total_quantity: int
    quantity: int
    max_quantity_per_order: int
    not_directly_orderable: bool
    separate_order_required: bool
    processing_required: bool


@dataclass(frozen=True)
class ArticleCompilationItem:
    article: Article
    fixed_quantity: int | None = None

    def __post_init__(self) -> None:
        if (self.fixed_quantity is not None) and (self.fixed_quantity < 1):
            raise ValueError(
                'Fixed quantity, if given, must be a positive number.'
            )

    def has_fixed_quantity(self) -> bool:
        return self.fixed_quantity is not None


class ArticleCompilation:
    def __init__(
        self, items: list[ArticleCompilationItem] | None = None
    ) -> None:
        self._items: list[ArticleCompilationItem] = []

        if items is not None:
            self._items.extend(items)

    def append(self, item: ArticleCompilationItem) -> ArticleCompilation:
        return ArticleCompilation(self._items + [item])

    def __iter__(self) -> Iterator[ArticleCompilationItem]:
        return iter(self._items)

    def is_empty(self) -> bool:
        return not self._items
