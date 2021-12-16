"""
:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from tests.helpers import log_in_user


@pytest.fixture(scope='package')
def party_admin(make_admin):
    permission_ids = {
        'admin.access',
        'party.create',
        'party.update',
        'party.view',
    }
    admin = make_admin('PartyAdmin', permission_ids)
    log_in_user(admin.id)
    return admin


@pytest.fixture(scope='package')
def party_admin_client(make_client, admin_app, party_admin):
    return make_client(admin_app, user_id=party_admin.id)
