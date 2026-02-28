#!/bin/bash

# Wait for Postgres to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"

# Run migrations
echo "Running migrations..."
python src/manage.py makemigrations
python src/manage.py migrate

# Create superuser if not exists
echo "Creating superuser..."
python src/manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser 'admin' created.")
else:
    print("Superuser 'admin' already exists.")
EOF

echo "Initialization complete."
