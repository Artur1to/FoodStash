# FoodStash

## Запуск в PyCharm

Открой этот проект с интерпретатором `FoodStash2\.venv\Scripts\python.exe`. В конфигурации Python укажи скрипт `manage.py`, параметр `runserver` и папку с `manage.py` как рабочую директорию. Сайт откроется на [localhost:8000](http://localhost:8000).

После установки зависимостей или обновления моделей выполни из папки с `manage.py`:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

Локально Django использует `db.sqlite3`, папку `media` и настройки из `.env`. Для чистой установки задай в `.env` свой `DJANGO_SECRET_KEY`. Настройки Яндекс Почты задаются через `YANDEX_SMTP_USER` и `YANDEX_SMTP_APP_PASSWORD`.

## Vercel и Neon

[Публичный сайт FoodStash](https://foodstash-recipes.vercel.app/)

В продакшене Vercel передаёт `DATABASE_URL` для Neon и `BLOB_READ_WRITE_TOKEN` для Vercel Blob. Ключ Django и доступ к Яндекс Почте хранятся в переменных окружения проекта Vercel.

Если релиз добавляет миграции, выполни их в Neon перед публикацией из связанной с Vercel папки проекта. Затем разверни сайт:

```powershell
vercel env run --environment production -- ..\.venv\Scripts\python.exe -B -c "import os,runpy; os.environ['FOODSTASH_DATABASE_URL']=os.environ['DATABASE_URL_UNPOOLED']; runpy.run_path('manage.py', run_name='__main__')" migrate --noinput
vercel deploy --prod
```

Команда `import_local_site` предназначена для первичного переноса в пустую базу. Локальный сайт и опубликованный сайт после переноса используют отдельные базы.
