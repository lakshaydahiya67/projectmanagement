web: gunicorn projectmanagement.wsgi:application --log-file -
worker: celery -A projectmanagement worker --loglevel=info
beat: celery -A projectmanagement beat --loglevel=info
