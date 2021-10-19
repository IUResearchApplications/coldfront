from django.contrib.messages import constants as messages

#------------------------------------------------------------------------------
# ColdFront logging config
#------------------------------------------------------------------------------

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
            'filename': './logs/core/allocation/allocation.log',
            'formatter': 'custom',
            'when': 'midnight',
        },
        'user': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': './logs/core/user/user.log',
            'formatter': 'custom',
            'when': 'midnight',
        },
        'project': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': './logs/core/project/project.log',
            'formatter': 'custom',
            'when': 'midnight',
        },
        'utils': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': './logs/core/utils/utils.log',
            'formatter': 'custom',
            'when': 'midnight',
        },
        'coldfront': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': './logs/coldfront/coldfront.log',
            'formatter': 'custom',
            'when': 'midnight',
        },
        'ldap_user_search': {
            'class': 'coldfront.config.modified_handlers.TimedRotatingFileHandler',
            'filename': './logs/plugins/ldap_user_search/ldap_user_search.log',
            'formatter': 'custom',
            'when': 'midnight',
        },
    },
    'root': {
        'handlers': ['coldfront', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'coldfront.core.allocation': {
            'handlers': ['allocation'],
            'level': 'INFO',
            'propagate': True,
        },
        'coldfront.core.user': {
            'handlers': ['user'],
            'level': 'INFO',
            'propagate': True,
        },
        'coldfront.core.project': {
            'handlers': ['project'],
            'level': 'INFO',
            'propagate': True,
        },
        'coldfront.core.utils': {
            'handlers': ['utils'],
            'level': 'INFO',
            'propagate': True,
        },
        'coldfront.plugins.ldap_user_search': {
            'handlers': ['ldap_user_search'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
