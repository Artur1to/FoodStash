import os
import uuid
from datetime import datetime
from unidecode import unidecode
from django.utils.text import slugify


def latin_filename(instance, filename):
    """
    Превращает любое имя файла в латиницу + добавляет уникальный суффикс.
    Пример: 'изображение.png' → 'izobrazhenie_20260925_abc123.png'
    """
    ext = filename.split('.')[-1].lower()
    name = filename.rsplit('.', 1)[0]

    # Транслитерируем в латиницу
    name = unidecode(name)
    # Оставляем только буквы/цифры/дефисы
    name = slugify(name)[:50] or 'file'

    # Уникальный суффикс, чтобы файлы не перезаписывались
    unique = uuid.uuid4().hex[:8]
    date = datetime.now().strftime('%Y%m%d')

    return f'{name}_{date}_{unique}.{ext}'