python3 manage.py makemigrations
python3 manage.py migrate
python manage.py collectstatic
cp -r /app/collected_static/. /backend_static/static/