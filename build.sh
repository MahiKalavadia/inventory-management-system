set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input

python manage.py loaddata suppliers.json
python manage.py loaddata users.json
python manage.py loaddata inventory.json
python manage.py loaddata orders.json.gz
python manage.py loaddata purchases.json