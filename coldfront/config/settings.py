import os
import environ
from split_settings.tools import optional, include
from coldfront.config.env import ENV, PROJECT_ROOT

# ColdFront split settings
coldfront_configs = [
    'base.py',
    'database.py',
    'auth.py',
    'logging.py',
    'core.py',
    'plugins/cas_login.py',
]

if ENV.bool('EMAIL_ENABLED', default=False):
    coldfront_configs.append('email.py')

# ColdFront plugin settings
plugin_configs = {
    'PLUGIN_SLURM': 'plugins/slurm.py',
    'PLUGIN_IQUOTA': 'plugins/iquota.py',
    'PLUGIN_FREEIPA': 'plugins/freeipa.py',
    'PLUGIN_SYSMON': 'plugins/system_montior.py',
    'PLUGIN_XDMOD': 'plugins/xdmod.py',
    'PLUGIN_AUTH_OIDC': 'plugins/openid.py',
    'PLUGIN_AUTH_LDAP': 'plugins/ldap.py',
    'PLUGIN_LDAP_USER_SEARCH': 'plugins/ldap_user_search.py',
    'PLUGIN_LDAP_USER_INFO': 'plugins/ldap_user_info.py',
    'PLUGIN_CAS': 'plugins/cas_login.py',
    'PLUGIN_ADVANCED_EXPORTING': 'plugins/advanced_exporting.py'
}

# This allows plugins to be enabled via environment variables. Can alternatively
# add the relevant configs to local_settings.py
for key, pc in plugin_configs.items():
    if ENV.bool(key, default=False):
        coldfront_configs.append(pc)

# Local settings overrides
local_configs = [
    # Local settings relative to coldfront.config package
    'local_settings.py',

    # System wide settings for production deployments
    '/etc/coldfront/local_settings.py',

    # Local settings relative to coldfront project root
    PROJECT_ROOT('local_settings.py')
]

if ENV.str('COLDFRONT_CONFIG', default='') != '':
    # Local settings from path specified via environment variable
    local_configs.append(environ.Path(ENV.str('COLDFRONT_CONFIG'))())

for lc in local_configs:
    coldfront_configs.append(optional(lc))

include(*coldfront_configs)
