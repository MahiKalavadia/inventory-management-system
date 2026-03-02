set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
gunzip -c data.json.gz > data.json
python manage.py loaddata data.json
python manage.py loaddata users.json