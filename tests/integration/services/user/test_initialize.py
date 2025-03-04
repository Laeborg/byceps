"""
:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.authorization import authz_service
from byceps.services.user import (
    user_command_service,
    user_log_service,
    user_service,
)


@pytest.fixture(scope='module')
def admin_user(make_user):
    return make_user()


@pytest.fixture(scope='module')
def uninitialized_user_created_online(make_user):
    return make_user(initialized=False)


@pytest.fixture(scope='module')
def uninitialized_user_created_at_party_checkin_by_admin(make_user):
    return make_user(initialized=False)


@pytest.fixture(scope='module')
def already_initialized_user(make_user):
    return make_user('AlreadyInitialized')


@pytest.fixture()
def role(
    admin_app,
    uninitialized_user_created_online,
    uninitialized_user_created_at_party_checkin_by_admin,
    already_initialized_user,
):
    role = authz_service.create_role('board_user', 'Board User').unwrap()

    yield role

    for user in {
        uninitialized_user_created_online,
        uninitialized_user_created_at_party_checkin_by_admin,
        already_initialized_user,
    }:
        authz_service.deassign_all_roles_from_user(user.id)

    authz_service.delete_role(role.id)


def test_initialize_account_as_user(
    admin_app, role, uninitialized_user_created_online
):
    user = uninitialized_user_created_online

    user_before = user_service.get_db_user(user.id)
    assert not user_before.initialized

    log_entries_before = user_log_service.get_entries_for_user(user_before.id)
    assert len(log_entries_before) == 1  # user creation

    role_ids_before = authz_service.find_role_ids_for_user(user.id)
    assert role_ids_before == set()

    # -------------------------------- #

    user_command_service.initialize_account(user.id)

    # -------------------------------- #

    user_after = user_service.get_db_user(user.id)
    assert user_after.initialized

    log_entries_after = user_log_service.get_entries_for_user(user_after.id)
    assert len(log_entries_after) == 3

    user_enabled_log_entry = log_entries_after[1]
    assert user_enabled_log_entry.event_type == 'user-initialized'
    assert user_enabled_log_entry.data == {}

    role_assigned_log_entry = log_entries_after[2]
    assert role_assigned_log_entry.event_type == 'role-assigned'
    assert role_assigned_log_entry.data == {
        'role_id': 'board_user',
    }

    role_ids_after = authz_service.find_role_ids_for_user(user.id)
    assert role_ids_after == {'board_user'}


def test_initialize_account_as_admin(
    admin_app,
    role,
    uninitialized_user_created_at_party_checkin_by_admin,
    admin_user,
):
    user = uninitialized_user_created_at_party_checkin_by_admin

    user_before = user_service.get_db_user(user.id)
    assert not user_before.initialized

    log_entries_before = user_log_service.get_entries_for_user(user_before.id)
    assert len(log_entries_before) == 1  # user creation

    role_ids_before = authz_service.find_role_ids_for_user(user.id)
    assert role_ids_before == set()

    # -------------------------------- #

    user_command_service.initialize_account(user.id, initiator_id=admin_user.id)

    # -------------------------------- #

    user_after = user_service.get_db_user(user.id)
    assert user_after.initialized

    log_entries_after = user_log_service.get_entries_for_user(user_after.id)
    assert len(log_entries_after) == 3

    user_enabled_log_entry = log_entries_after[1]
    assert user_enabled_log_entry.event_type == 'user-initialized'
    assert user_enabled_log_entry.data == {
        'initiator_id': str(admin_user.id),
    }

    role_assigned_log_entry = log_entries_after[2]
    assert role_assigned_log_entry.event_type == 'role-assigned'
    assert role_assigned_log_entry.data == {
        'initiator_id': str(admin_user.id),
        'role_id': 'board_user',
    }

    role_ids_after = authz_service.find_role_ids_for_user(user.id)
    assert role_ids_after == {'board_user'}


def test_initialize_already_initialized_account(
    admin_app, role, already_initialized_user, admin_user
):
    user = already_initialized_user

    user_before = user_service.get_db_user(user.id)
    assert user_before.initialized

    log_entries_before = user_log_service.get_entries_for_user(user_before.id)
    assert len(log_entries_before) == 1  # user creation

    # -------------------------------- #

    with pytest.raises(ValueError):
        user_command_service.initialize_account(
            user.id, initiator_id=admin_user.id
        )

    # -------------------------------- #

    user_after = user_service.get_db_user(user.id)
    assert user_after.initialized  # still initialized

    log_entries_after = user_log_service.get_entries_for_user(user_after.id)
    assert len(log_entries_after) == 1  # no additional user log entries
