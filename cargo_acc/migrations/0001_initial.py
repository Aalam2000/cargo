# Generated by Django 4.2 on 2024-10-04 15:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Cargo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cargo_code", models.CharField(max_length=20, unique=True)),
                (
                    "departure_place",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "destination_place",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "weight",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "volume",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "insurance",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                ("dimensions", models.CharField(blank=True, max_length=30, null=True)),
                ("shipping_date", models.DateField(blank=True, null=True)),
                ("delivery_date", models.DateField(blank=True, null=True)),
                (
                    "delivery_time",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CargoStatus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20, unique=True)),
                ("description", models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="CargoType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20, unique=True)),
                ("description", models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="CarrierCompany",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("registration", models.CharField(max_length=50)),
                (
                    "description",
                    models.CharField(blank=True, max_length=500, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Client",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("client_code", models.CharField(max_length=20, unique=True)),
                (
                    "description",
                    models.CharField(blank=True, max_length=500, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("registration", models.CharField(max_length=50)),
                (
                    "description",
                    models.CharField(blank=True, max_length=500, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Image",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image_file",
                    models.ImageField(
                        default="img/default_image.jpg", upload_to="img/"
                    ),
                ),
                ("upload_date", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="PackagingType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20, unique=True)),
                ("description", models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Warehouse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("address", models.CharField(blank=True, max_length=500, null=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.company",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("license_plate", models.CharField(max_length=20, unique=True)),
                ("model", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "current_status",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "carrier_company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.carriercompany",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TransportBill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bill_code", models.CharField(max_length=20, unique=True)),
                (
                    "departure_place",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "destination_place",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("departure_date", models.DateField()),
                ("arrival_date", models.DateField(blank=True, null=True)),
                ("cargos", models.ManyToManyField(to="cargo_acc.cargo")),
                (
                    "carrier_company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.carriercompany",
                    ),
                ),
                (
                    "vehicle",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.vehicle",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("product_code", models.CharField(max_length=30, unique=True)),
                ("record_date", models.DateField(blank=True, null=True)),
                (
                    "cargo_description",
                    models.CharField(blank=True, max_length=500, null=True),
                ),
                (
                    "departure_place",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "destination_place",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "weight",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "volume",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "insurance",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                ("dimensions", models.CharField(blank=True, max_length=30, null=True)),
                ("shipping_date", models.DateField(blank=True, null=True)),
                ("delivery_date", models.DateField(blank=True, null=True)),
                (
                    "delivery_time",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "cargo_status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.cargostatus",
                    ),
                ),
                (
                    "cargo_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.cargotype",
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.client",
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.company",
                    ),
                ),
                ("images", models.ManyToManyField(to="cargo_acc.image")),
                (
                    "packaging_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.packagingtype",
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.warehouse",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="client",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cargo_acc.company"
            ),
        ),
        migrations.CreateModel(
            name="CargoMovement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "transfer_place",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("transfer_date", models.DateTimeField()),
                (
                    "cargo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="cargo_acc.cargo",
                    ),
                ),
                (
                    "from_transport_bill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="from_transport_bill",
                        to="cargo_acc.transportbill",
                    ),
                ),
                (
                    "to_transport_bill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="to_transport_bill",
                        to="cargo_acc.transportbill",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="cargo",
            name="cargo_status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cargo_acc.cargostatus"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="cargo_acc.client"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="images",
            field=models.ManyToManyField(to="cargo_acc.image"),
        ),
        migrations.AddField(
            model_name="cargo",
            name="packaging_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="cargo_acc.packagingtype",
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="products",
            field=models.ManyToManyField(to="cargo_acc.product"),
        ),
    ]