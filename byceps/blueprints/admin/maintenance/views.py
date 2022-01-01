"""
byceps.blueprints.admin.maintenance.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime, timedelta

from flask_babel import gettext

from ....services.user import log_service as user_log_service
from ....services.verification_token import (
    service as verification_token_service,
)
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_success
from ....util.framework.templating import templated
from ....util.views import permission_required, respond_no_content


blueprint = create_blueprint('maintenance_admin', __name__)


@blueprint.get('')
@permission_required('admin.maintain')
@templated
def index():
    """Show maintenance overview."""
    verification_token_counts_by_purpose = (
        verification_token_service.count_tokens_by_purpose()
    )

    verification_token_counts_by_purpose_name = {
        purpose.name: count
        for purpose, count in verification_token_counts_by_purpose.items()
    }

    verification_token_total = sum(
        verification_token_counts_by_purpose.values()
    )

    return {
        'verification_token_counts_by_purpose_name': verification_token_counts_by_purpose_name,
        'verification_token_total': verification_token_total,
    }


@blueprint.post('/delete_old_login_log_entries')
@permission_required('admin.maintain')
@respond_no_content
def delete_old_login_log_entries():
    """Delete login log entries older than a given number of days."""
    now = datetime.utcnow()
    minimum_age_in_days = 90
    occurred_before = now - timedelta(days=minimum_age_in_days)

    num_deleted = user_log_service.delete_user_login_log_entries(
        occurred_before
    )

    flash_success(
        gettext(
            'Deleted %(num_deleted)s login log entries older than %(minimum_age_in_days)s days.',
            num_deleted=num_deleted,
            minimum_age_in_days=minimum_age_in_days,
        )
    )


@blueprint.post('/delete_old_verification_tokens')
@permission_required('admin.maintain')
@respond_no_content
def delete_old_verification_tokens():
    """Delete verification tokens older than a given number of days."""
    now = datetime.utcnow()
    minimum_age_in_days = 7
    created_before = now - timedelta(days=minimum_age_in_days)

    num_deleted = verification_token_service.delete_old_tokens(created_before)

    flash_success(
        gettext(
            'Deleted %(num_deleted)s verification tokens older than %(minimum_age_in_days)s days.',
            num_deleted=num_deleted,
            minimum_age_in_days=minimum_age_in_days,
        )
    )
