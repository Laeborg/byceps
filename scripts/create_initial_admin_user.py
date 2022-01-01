#!/usr/bin/env python

"""Create an initial user with admin privileges to begin BYCEPS setup.

:Copyright: 2006-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations
from typing import Iterable, Sequence

import click

from byceps.services.authorization import service as authorization_service
from byceps.services.authorization.transfer.models import RoleID
from byceps.services.user import (
    command_service as user_command_service,
    creation_service as user_creation_service,
    email_address_service as user_email_address_service,
)
from byceps.services.user.transfer.models import User
from byceps.typing import UserID

from _util import call_with_app_context


@click.command()
@click.option('--screen_name', prompt=True)
@click.option('--email_address', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def execute(screen_name, email_address, password) -> None:
    click.echo(f'Creating user "{screen_name}" ... ', nl=False)
    user = _create_user(screen_name, email_address, password)
    click.secho('done.', fg='green')

    click.echo(f'Initializing user "{screen_name}" ... ', nl=False)
    user_command_service.initialize_account(user.id)
    click.secho('done.', fg='green')

    user_email_address_service.confirm_email_address(user.id, email_address)

    role_ids = _get_role_ids()
    click.echo(
        f'Assigning {len(role_ids)} roles to user "{screen_name}" ... ',
        nl=False,
    )
    _assign_roles_to_user(role_ids, user.id)
    click.secho('done.', fg='green')


def _create_user(screen_name: str, email_address: str, password: str) -> User:
    try:
        user, event = user_creation_service.create_user(
            screen_name, email_address, password
        )
        return user
    except ValueError as e:
        raise click.UsageError('User creation failed: {e}')


def _get_role_ids() -> set[RoleID]:
    return authorization_service.get_all_role_ids()


def _assign_roles_to_user(role_ids: set[RoleID], user_id: UserID) -> None:
    for role_id in role_ids:
        authorization_service.assign_role_to_user(role_id, user_id)


if __name__ == '__main__':
    call_with_app_context(execute)
