from coldfront.config.base import INSTALLED_APPS
from coldfront.config.env import ENV


INSTALLED_APPS += [
    'coldfront.plugins.academic_analytics',
]

ACADEMIC_ANALYTICS_API_KEY = ENV.str('ACADEMIC_ANALYTICS_API_KEY')
ACADEMIC_ANALYTICS_API_BASE_ADDRESS = ENV.str('ACADEMIC_ANALYTICS_API_BASE_ADDRESS')
ACADEMIC_ANALYTICS_FORMULA = ENV.str('ACADEMIC_ANALYTICS_FORMULA')
ORACLE_DB_USER = ENV.str('ORACLE_DB_USER')
ORACLE_DB_PASSWORD = ENV.str('ORACLE_DB_PASSWORD')
ORACLE_DB_DSN = ENV.str('ORACLE_DB_DSN')
ORACLE_DB_QUERY = ENV.str('ORACLE_DB_QUERY')
