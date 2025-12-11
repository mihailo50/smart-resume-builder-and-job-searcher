web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread --timeout 120
release: python manage.py collectstatic --noinput && python manage.py migrate --noinput

