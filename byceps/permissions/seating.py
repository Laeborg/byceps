"""
byceps.permissions.seating
~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext

from byceps.util.authorization import register_permissions


register_permissions(
    'seating',
    [
        ('administrate', lazy_gettext('Administrate seating')),
        ('view', lazy_gettext('View seating administration')),
    ],
)
