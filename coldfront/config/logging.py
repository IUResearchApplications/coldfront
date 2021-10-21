from os import path

from django.contrib.messages import constants as messages
from coldfront.core.utils.common import import_from_settings

#------------------------------------------------------------------------------
# ColdFront logging config
#------------------------------------------------------------------------------

LOG_LEVEL = import_from_settings(
    'LOG_LEVEL', 'INFO')

LOG_BASE_DIR = import_from_settings(
    'LOG_BASE_DIR', './logs')

MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'custom': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'custom',
        },
        'allocation': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': path.join(LOG_BASE_DIR, 'core/allocation/allocation.log'),
            'formatter': 'custom',
            'when': 'midnight',
        },
        'user': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': path.join(LOG_BASE_DIR, 'core/user/user.log'),
            'formatter': 'custom',
            'when': 'midnight',
        },
        'project': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': path.join(LOG_BASE_DIR, 'core/project/project.log'),
            'formatter': 'custom',
            'when': 'midnight',
        },
        'utils': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': path.join(LOG_BASE_DIR, 'core/utils/utils.log'),
            'formatter': 'custom',
            'when': 'midnight',
        },
        'coldfront': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': path.join(LOG_BASE_DIR, 'coldfront/coldfront.log'),
            'formatter': 'custom',
            'when': 'midnight',
        },
        'ldap_user_search': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': path.join(LOG_BASE_DIR, 'plugins/ldap_user_search/ldap_user_search.log'),
            'formatter': 'custom',
            'when': 'midnight',
        },
    },
    'root': {
        'handlers': ['coldfront', 'console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
        },
        'coldfront.core.allocation': {
            'handlers': ['allocation'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'coldfront.core.user': {
            'handlers': ['user'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'coldfront.core.project': {
            'handlers': ['project'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'coldfront.core.utils': {
            'handlers': ['utils'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'coldfront.plugins.ldap_user_search': {
            'handlers': ['ldap_user_search'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
}
