"""
:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.authorization import service


def test_assign_permission_to_role(admin_app, permission_tickle_mortals, role):
    permission = permission_tickle_mortals

    role_permission_ids_before = get_permission_ids_for_role(role)
    assert permission.id not in role_permission_ids_before

    service.assign_permission_to_role(permission.id, role.id)

    role_permission_ids_after = get_permission_ids_for_role(role)
    assert permission.id in role_permission_ids_after

    # Clean up.
    service.deassign_permission_from_role(permission.id, role.id)


def test_deassign_permission_from_role(
    admin_app, permission_tickle_mortals, role
):
    permission = permission_tickle_mortals

    service.assign_permission_to_role(permission.id, role.id)

    role_permission_ids_before = get_permission_ids_for_role(role)
    assert permission.id in role_permission_ids_before

    service.deassign_permission_from_role(permission.id, role.id)

    role_permission_ids_after = get_permission_ids_for_role(role)
    assert permission.id not in role_permission_ids_after


@pytest.fixture
def role():
    role = service.create_role('demigod', 'Demigod')
    yield role
    service.delete_role(role.id)


def get_permission_ids_for_role(role):
    return service.get_permission_ids_for_role(role.id)
