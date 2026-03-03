set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input

python manage.py loaddata data.json.gz
python manage.py loaddata users.json