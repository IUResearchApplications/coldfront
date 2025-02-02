from coldfront.config.base import INSTALLED_APPS
from coldfront.config.env import ENV

INSTALLED_APPS += [
    'coldfront.plugins.geode_project',
]

GEODE_PROJECT_EMAIL = ENV.str('GEODE_PROJECT_EMAIL')
GEODE_PROJECT_ALLOCATED_QUANTITY_THRESHOLD = ENV.int('GEODE_PROJECT_ALLOCATED_QUANTITY_THRESHOLD', 10)
ENABLE_GEODE_PROJECT_LDAP_INTEGRATION = ENV.str('ENABLE_GEODE_PROJECT_LDAP_INTEGRATION', False)
if ENABLE_GEODE_PROJECT_LDAP_INTEGRATION:
    LDAP_GEODE_PROJECT_SERVER_URI = ENV.str('LDAP_GEODE_PROJECT_SERVER_URI')
    LDAP_GEODE_PROJECT_BASE_DN = ENV.str('LDAP_GEODE_PROJECT_BASE_DN')
    LDAP_GEODE_PROJECT_BIND_DN = ENV.str('LDAP_GEODE_PROJECT_BIND_DN')
    LDAP_GEODE_PROJECT_BIND_PASSWORD = ENV.str('LDAP_GEODE_PROJECT_BIND_PASSWORD')
    LDAP_GEODE_PROJECT_CONNECT_TIMEOUT = ENV.float('LDAP_GEODE_PROJECT_CONNECT_TIMEOUT', 2.5)
    LDAP_GEODE_PROJECT_GROUP_TYPE = ENV.int('LDAP_GEODE_PROJECT_GROUP_TYPE')
    LDAP_GEODE_PROJECT_USER_ACCOUNT_TEMPLATE = ENV.str('LDAP_GEODE_PROJECT_USER_ACCOUNT_TEMPLATE')
    LDAP_GEODE_PROJECT_GROUP_TEMPLATE = ENV.str('LDAP_GEODE_PROJECT_GROUP_TEMPLATE')
    LDAP_GEODE_ALL_USERS_GROUP = ENV.str('LDAP_GEODE_ALL_USERS_GROUP')
