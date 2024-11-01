import csv
from django.core.management.base import BaseCommand
from cargo_acc.models import Client, Company

class Command(BaseCommand):
    help = 'Загружает клиентов из колонки C в файле test/new_nakl.csv'

    def handle(self, *args, **kwargs):
        # Указываем путь к файлу CSV
        csv_path = 'test/new_nakl.csv'

        # Ищем или создаём компанию "Наша Компания"
        company, _ = Company.objects.get_or_create(name='Наша Компания')

        # Создаем пустой набор для уникальных клиентов
        unique_clients = set()

        # Читаем файл и извлекаем данные из колонки "КЛИЕНТ"
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                client_code = row['КЛИЕНТ'].strip()  # Убираем пробелы
                if client_code:  # Добавляем только непустые значения
                    unique_clients.add(client_code)

        total_clients = len(unique_clients)  # Общее количество клиентов
        loaded_count = 0  # Счётчик загруженных клиентов

        # Загружаем клиентов в базу данных и отображаем прогресс
        for client_code in unique_clients:
            Client.objects.update_or_create(
                client_code=client_code,
                defaults={'company': company, 'description': 'Клиент'}
            )
            loaded_count += 1  # Увеличиваем счётчик загруженных клиентов

            # Вычисляем и отображаем процент выполнения
            percent_complete = (loaded_count / total_clients) * 100
            self.stdout.write(
                f'Загружено: {loaded_count}/{total_clients} клиентов ({percent_complete:.2f}%)'
            )

        self.stdout.write(self.style.SUCCESS('Загрузка клиентов завершена!'))