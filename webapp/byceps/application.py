# -*- coding: utf-8 -*-

"""
byceps.application
~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from flask import Flask, g
import jinja2

from .blueprints.snippet.init import add_routes_for_snippets
from .config import SiteMode
from .database import db
from .util import dateformat
from .util.framework import load_config, register_blueprint
from .util.l10n import set_locale


BLUEPRINTS = [
    ('authorization',       '/authorization',       None          ),
    ('authorization_admin', '/admin/authorization', SiteMode.admin),
    ('board',               '/board',               None          ),
    ('brand',               None,                   None          ),
    ('core',                '/core',                None          ),
    ('orga',                '/orgas',               None          ),
    ('orga_admin',          '/admin/orgas',         SiteMode.admin),
    ('party',               None,                   None          ),
    ('party_admin',         '/admin/parties',       SiteMode.admin),
    ('seating',             '/seating',             None          ),
    ('snippet',             '/snippets',            None          ),
    ('snippet_admin',       '/admin/snippets',      SiteMode.admin),
    ('terms',               '/terms',               None          ),
    ('terms_admin',         '/admin/terms',         SiteMode.admin),
    ('user',                '/users',               None          ),
    ('user_admin',          '/admin/users',         SiteMode.admin),
    ('user_group',          '/user_groups',         None          ),
]


def create_app(environment_name, *, initialize=True):
    """Create the actual Flask application."""
    app = Flask(__name__)

    load_config(app, environment_name)

    # Throw an exception when an undefined name is referenced in a template.
    app.jinja_env.undefined = jinja2.StrictUndefined

    # Set the locale.
    set_locale(app.config['LOCALE'])  # Fail if not configured.

    # Initialize database.
    db.init_app(app)

    mode = get_site_mode(app)
    app.extensions['byceps'] = {
        'mode': mode,
    }

    register_blueprints(app, mode)

    dateformat.register_template_filters(app)

    if initialize:
        with app.app_context():
            app.party_id = get_current_party_id(app)
            add_routes_for_snippets()

    return app


def get_site_mode(app):
    """Return the mode the site should run in."""
    value = app.config.get('MODE')
    if value is None:
        raise Exception('No site mode configured.')

    try:
        return SiteMode[value]
    except KeyError:
        raise Exception('Invalid site mode "{}" configured.'.format(value))


def register_blueprints(app, current_mode):
    """Register the blueprints that are relevant for the current mode."""
    for name, url_prefix, mode in BLUEPRINTS:
        if mode is None or mode == current_mode:
            register_blueprint(app, name, url_prefix)


def get_current_party_id(app):
    """Determine the current party from the configuration."""
    party_id = app.config.get('PARTY')
    if party_id is None:
        raise Exception('No party configured.')

    return party_id
