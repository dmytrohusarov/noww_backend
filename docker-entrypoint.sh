# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput


mkdir /var/backups
apt-get update
apt-get -y install postgresql-client
python manage.py dbbackup -q -z -d default

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Load dump data
echo "Load database data"
python manage.py loaddata service_dump.json

# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000

