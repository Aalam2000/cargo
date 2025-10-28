# accounts/management/commands/link_clients.py
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from cargo_acc.models import Client

class Command(BaseCommand):
    help = "Связывает пользователей с клиентами по полю client_code"

    def handle(self, *args, **options):
        linked, skipped = 0, 0

        for user in CustomUser.objects.filter(role="Client"):
            if not user.client_code:
                skipped += 1
                continue

            client = Client.objects.filter(client_code=user.client_code).first()
            if client:
                user.linked_client = client
                user.save(update_fields=["linked_client"])
                linked += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Связано: {linked}, пропущено: {skipped}"))
