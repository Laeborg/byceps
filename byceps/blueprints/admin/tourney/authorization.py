"""
byceps.blueprints.admin.tourney.authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.util.authorization import create_permission_enum


TourneyCategoryPermission = create_permission_enum('tourney_category', [
    'create',
    'update',
    'view',
])
