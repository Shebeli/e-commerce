# Generated by Django 5.0.6 on 2024-07-28 12:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_modified'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='main_variant',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='main_variant_of', to='product.productvariant'),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='product.product'),
        ),
    ]
