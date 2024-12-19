#rm users/migrations/0*.py recipes/migrations/0*.py
python3 manage.py makemigrations
python3 manage.py migrate
python manage.py collectstatic