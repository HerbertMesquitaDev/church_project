import os
from pathlib import Path
from django.contrib.messages import constants as msg_constants

# ── Carrega variáveis do .env ──────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
except ImportError:
    pass  # python-dotenv não instalado — usa variáveis de ambiente do sistema

BASE_DIR = Path(__file__).resolve().parent.parent


# ── Segurança ──────────────────────────────────────────────
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-change-this-in-production-use-env-variable'
)
if 'django-insecure' in SECRET_KEY and os.getenv('DEBUG', 'True').lower() not in ('true', '1', 'yes'):
    raise ValueError(
        "SECRET_KEY inválida para produção. "
        "Defina uma chave segura no arquivo .env"
    )

_debug_env = os.getenv('DEBUG', 'True')
DEBUG = str(_debug_env).lower() in ('true', '1', 'yes')

_allowed = os.getenv('ALLOWED_HOSTS', '')
if _allowed.strip() == '*' or not _allowed.strip():
    # Em desenvolvimento, permite todos os hosts locais automaticamente
    ALLOWED_HOSTS = ['*'] if DEBUG else ['localhost', '127.0.0.1', '[::1]']
else:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

# Em desenvolvimento, sempre garante hosts locais
if DEBUG and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '[::1]', '0.0.0.0']


# ── Configurações de produção (ativadas quando DEBUG=False) ─
if not DEBUG:
    SECURE_SSL_REDIRECT            = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    SECURE_BROWSER_XSS_FILTER      = True
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    X_FRAME_OPTIONS                = 'DENY'
    ADMINS = [
        (
            os.getenv('SUPER_USER', 'Administrador'),
            os.getenv('ADMIN_EMAIL', ''),
        )
    ]


# ── Apps ───────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_session_timeout',
    'django.contrib.sitemaps',
    'rest_framework',
    'rest_framework.authtoken',
    'tinymce',
    'core',
    'api',
    'events',
    'members',
    'agenda',
    'ebd',
    'cells',
    'birthdays',
    'courses',
    'tenants',
    'superadmin',
]


# ── Middleware ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
    'tenants.middleware.TenantMiddleware',   
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.VisitTrackingMiddleware',
]

ROOT_URLCONF = 'church_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_info',
                'core.context_processors.pending_visitor_count',
                'core.context_processors.pending_cell_count',
                'core.context_processors.pending_delete_count',
                'core.context_processors.pending_prayer_count',
                'core.context_processors.pending_testimony_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'church_project.wsgi.application'

# ── Banco de dados ─────────────────────────────────────────
_db_engine = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')

if not os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE':   _db_engine,
            'NAME':     os.getenv('DB_NAME'),
            'USER':     os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST':     os.getenv('DB_HOST', 'localhost'),
            'PORT':     os.getenv('DB_PORT', '5432'),
        }
    }

# ── Cache (Redis) ───────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ── Autenticação ───────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'core.backends.EmailBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/membros/login/'


# ── Internacionalização ────────────────────────────────────
LANGUAGE_CODE = 'pt-BR'
TIME_ZONE     = 'America/Campo_Grande'
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True


# ── Arquivos estáticos e mídia ─────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── Sessão e timeout de inatividade ───────────────────────
SESSION_EXPIRE_SECONDS             = int(os.getenv('SESSION_EXPIRE_SECONDS', 1800))
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_TIMEOUT_REDIRECT           = '/membros/timeout/'
SESSION_COOKIE_AGE                 = SESSION_EXPIRE_SECONDS


# ── E-mail ─────────────────────────────────────────────────
_default_email_backend = (
    'django.core.mail.backends.console.EmailBackend' if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_BACKEND       = os.getenv('EMAIL_BACKEND', _default_email_backend)
EMAIL_HOST          = os.getenv('EMAIL_HOST',     'smtp.gmail.com')
EMAIL_PORT          = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS       = str(os.getenv('EMAIL_USE_TLS', 'True')).lower() in ('true', '1')
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER',     '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.getenv('DEFAULT_FROM_EMAIL',  'noreply@suaigreja.com.br')
SERVER_EMAIL        = DEFAULT_FROM_EMAIL


# ── Mensagens Bootstrap ────────────────────────────────────
MESSAGE_TAGS = {
    msg_constants.DEBUG:   'alert-secondary',
    msg_constants.INFO:    'alert-info',
    msg_constants.SUCCESS: 'alert-success',
    msg_constants.WARNING: 'alert-warning',
    msg_constants.ERROR:   'alert-danger',
}


# ── Twilio 2FA ──────────────────────────────────────────────
TWILIO_ACCOUNT_SID  = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN   = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')


# ── Logging ────────────────────────────────────────────────
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name} {process:d} {thread:d} — {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} [{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_general': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_errors': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_general'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file_security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file_errors'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Logger para os apps do projeto
        'core': {'handlers': ['file_general'], 'level': 'INFO', 'propagate': True},
        'members': {'handlers': ['file_general', 'file_security'], 'level': 'INFO', 'propagate': True},
        'events': {'handlers': ['file_general'], 'level': 'INFO', 'propagate': True},
    },
    'root': {
        'handlers': ['console', 'file_errors'],
        'level': 'WARNING',
    },
}


# ── TinyMCE ────────────────────────────────────────────────
TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'menubar': 'file edit view insert format tools table',
    'plugins': (
        'advlist autolink lists link image charmap preview anchor '
        'searchreplace visualblocks code fullscreen '
        'insertdatetime media table code help wordcount'
    ),
    'toolbar': (
        'undo redo | styles | bold italic underline strikethrough | '
        'alignleft aligncenter alignright alignjustify | '
        'bullist numlist outdent indent | link image | '
        'forecolor backcolor removeformat | code fullscreen'
    ),
    'content_style': (
        'body { font-family: Helvetica, Arial, sans-serif; font-size: 14px; }'
    ),
    'language': 'pt_BR',
}


# ── Django REST Framework ──────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}