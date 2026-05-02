from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

_IMG_EXT   = ['jpg', 'jpeg', 'png', 'gif', 'webp']
_AUDIO_EXT = ['mp3', 'wav', 'ogg', 'm4a', 'aac']
_DOC_EXT   = ['pdf', 'doc', 'docx']

MAX_IMAGE_MB = 5
MAX_AUDIO_MB = 50
MAX_DOC_MB   = 20
MAX_FILE_MB  = 50


def _check_size(value, max_mb):
    if hasattr(value, 'size') and value.size > max_mb * 1024 * 1024:
        raise ValidationError(
            f'O arquivo não pode ser maior que {max_mb} MB. '
            f'Tamanho atual: {value.size / (1024 * 1024):.1f} MB.'
        )


def validate_image(value):
    FileExtensionValidator(allowed_extensions=_IMG_EXT)(value)
    _check_size(value, MAX_IMAGE_MB)


def validate_audio(value):
    FileExtensionValidator(allowed_extensions=_AUDIO_EXT)(value)
    _check_size(value, MAX_AUDIO_MB)


def validate_document(value):
    FileExtensionValidator(allowed_extensions=_DOC_EXT)(value)
    _check_size(value, MAX_DOC_MB)


def validate_generic_file(value):
    allowed = _IMG_EXT + _AUDIO_EXT + _DOC_EXT
    FileExtensionValidator(allowed_extensions=allowed)(value)
    _check_size(value, MAX_FILE_MB)
