from django.core.management.base import BaseCommand
from cargo_acc.services.currency_updater import update_all_rates

class Command(BaseCommand):
    help = "Загружает курсы EUR / RUB / CNY из бесплатных источников"

    def handle(self, *args, **kwargs):
        result = update_all_rates()
        for cur, rate in result.items():
            if rate != "ERROR":
                self.stdout.write(self.style.SUCCESS(f"{cur}: {rate}"))
            else:
                self.stdout.write(self.style.ERROR(f"{cur}: ERROR"))
