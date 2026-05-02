"""Settings para testes — usa SQLite em memória, sem dependência de PostgreSQL."""
from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desativa logging verboso nos testes
LOGGING = {}

# Senha simples para testes
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Sem arquivos de mídia reais
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
