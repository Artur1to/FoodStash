import mimetypes
import os
from functools import cached_property
from urllib.parse import quote

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.files.utils import validate_file_name
from vercel.blob import sync as blob


class VercelBlobStorage(Storage):
    @cached_property
    def origin(self):
        store_id = os.getenv('BLOB_STORE_ID', '')
        if not store_id:
            token = os.getenv('BLOB_READ_WRITE_TOKEN', '')
            if token.startswith('vercel_blob_rw_'):
                store_id = token.removeprefix('vercel_blob_rw_').partition('_')[0]
        store_id = store_id.removeprefix('store_')
        if not store_id.isascii() or not store_id.isalnum():
            raise ImproperlyConfigured('Connect a public Vercel Blob store.')
        return f'https://{store_id.lower()}.public.blob.vercel-storage.com'

    def _pathname(self, name):
        name = str(name).replace('\\', '/')
        validate_file_name(name, allow_relative_path=True)
        return f'media/{name}'

    def url(self, name):
        return f'{self.origin}/{quote(self._pathname(name))}'

    def exists(self, name):
        try:
            blob.head_blob(self.url(name))
        except blob.BlobNotFoundError:
            return False
        return True

    def _open(self, name, mode='rb'):
        if mode != 'rb':
            raise ValueError('Vercel Blob files can only be opened in binary read mode.')
        try:
            return ContentFile(blob.get_blob(self.url(name), access='public').body, name=name)
        except blob.BlobNotFoundError as exc:
            raise FileNotFoundError(name) from exc

    def _save(self, name, content):
        content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        blob.put_blob(self._pathname(name), content.read(), access='public', content_type=content_type)
        return name

    def size(self, name):
        return blob.head_blob(self.url(name)).size

    def delete(self, name):
        blob.delete_blob(self.url(name))
