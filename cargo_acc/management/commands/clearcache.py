from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Очистить весь кэш.'

    def handle(self, *args, **kwargs):
        cache.clear()
        self.stdout.write('Кэш очищен.')
