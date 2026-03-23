set -o errexit

pip install -r requirements.txt
python manage.py migrate
python manage.py import_bulk_products
python manage.py import_bulk_purchases
python manage.py import_bulk_orders
python manage.py import_bulk_stocklogs
