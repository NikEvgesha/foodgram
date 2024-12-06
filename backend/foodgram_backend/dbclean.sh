rm users/migrations/0*.py recipes/migrations/0*.py
rm db.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py import_csv