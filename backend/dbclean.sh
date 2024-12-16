rm users/migrations/0*.py recipes/migrations/0*.py
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py import_csv
python manage.py collectstatic
cp -r /app/collected_static/. /backend_static/static/