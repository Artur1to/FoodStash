import os
from pathlib import Path

import dj_database_url
from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.files.storage import FileSystemStorage
from django.core.management import BaseCommand, CommandError, call_command
from django.core.management.color import no_style
from django.db import connections, transaction

from recipes.models import Recipe, User
from recipes.storage import VercelBlobStorage


GENERATED_MODELS = ('auth.Permission', 'contenttypes.ContentType', 'recipes.Achievement')


class Command(BaseCommand):
    help = 'Copy the local SQLite site and its referenced media into a fresh PostgreSQL database and Vercel Blob.'

    def add_arguments(self, parser):
        parser.add_argument('--sqlite', type=Path, default=settings.BASE_DIR / 'db.sqlite3')
        parser.add_argument('--media-root', type=Path, default=settings.MEDIA_ROOT)

    def handle(self, *, sqlite, media_root, **options):
        if not sqlite.is_file():
            raise CommandError('The SQLite source file does not exist.')
        url = os.getenv('DATABASE_URL_UNPOOLED') or os.getenv('FOODSTASH_DATABASE_URL')
        if not url:
            raise CommandError('Set DATABASE_URL_UNPOOLED or FOODSTASH_DATABASE_URL for the target.')
        database = dj_database_url.parse(url, conn_max_age=0)
        if database['ENGINE'] != 'django.db.backends.postgresql':
            raise CommandError('The import target must be PostgreSQL.')

        config = connections.databases
        config['local_source'] = {
            **config['default'],
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': f'{sqlite.resolve().as_uri()}?mode=ro',
            'OPTIONS': {},
        }
        config['import_target'] = {**config['default'], **database}

        models = [
            model for model in apps.get_models()
            if model._meta.label != 'sessions.Session'
        ]
        with transaction.atomic(using='local_source'):
            media = self._media_files()
            objects = {
                model: self._serialize(model, 'local_source') for model in models
            }

        local_storage = FileSystemStorage(location=media_root)
        missing = [name for name in media if not local_storage.exists(name)]
        if missing:
            raise CommandError(f'Missing {len(missing)} referenced image(s), including {missing[0]}.')

        call_command('migrate', database='import_target', interactive=False, verbosity=1)
        self._copy_database(objects, models, media, local_storage)
        for model, rows in objects.items():
            self.stdout.write(f'{model._meta.label}: {len(rows)}')
        self.stdout.write(self.style.SUCCESS(f'Import verified. {len(media)} media files available.'))

    def _serialize(self, model, database):
        return serializers.serialize('python', model._base_manager.using(database).order_by('pk'))

    def _media_files(self):
        return sorted({
            name
            for model, field in ((Recipe, 'image'), (User, 'avatar'), (User, 'banner'))
            for name in model.objects.using('local_source').values_list(field, flat=True)
            if name
        })

    def _copy_database(self, objects, models, media, local_storage):
        database = 'import_target'
        generated = [apps.get_model(label) for label in GENERATED_MODELS]
        with transaction.atomic(using=database):
            connection = connections[database]
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(%s)', [198754203])
            identical = all(self._serialize(model, database) == rows for model, rows in objects.items())
            if not identical and any(
                model._base_manager.using(database).exists()
                for model in models if model not in generated
            ):
                raise CommandError('The target contains existing site data. Use a fresh PostgreSQL database.')

            remote_storage = VercelBlobStorage()
            for name in media:
                with local_storage.open(name, 'rb') as source:
                    if remote_storage.exists(name):
                        with remote_storage.open(name) as uploaded:
                            if uploaded.read() != source.read():
                                raise CommandError(f'Existing Blob differs from the source: {name}')
                    else:
                        remote_storage.save(name, source)
                        if remote_storage.size(name) != source.size:
                            raise CommandError(f'Blob size differs after upload: {name}')

            if identical:
                return
            for model in generated:
                model._base_manager.using(database).all().delete()
            for rows in objects.values():
                for item in serializers.deserialize('python', rows, using=database):
                    item.save(using=database)
            connection.check_constraints()
            with connection.cursor() as cursor:
                for statement in connection.ops.sequence_reset_sql(no_style(), models):
                    cursor.execute(statement)
            if any(self._serialize(model, database) != rows for model, rows in objects.items()):
                raise CommandError('PostgreSQL data differs from the SQLite snapshot.')
