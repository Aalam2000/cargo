# Миграции:

docker exec -it cargo_app python manage.py makemigrations accounts
docker exec -it cargo_app python manage.py migrate accounts
