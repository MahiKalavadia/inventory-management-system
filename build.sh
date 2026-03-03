set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input

gunzip -c data.json.gz > data.json
python manage.py loaddata ./data.json
python manage.py loaddata ./users.json