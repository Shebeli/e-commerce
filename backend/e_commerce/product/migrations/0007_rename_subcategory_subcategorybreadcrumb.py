# Generated by Django 5.1 on 2025-03-22 15:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_alter_subcategory_name_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SubCategory',
            new_name='SubCategoryBreadCrumb',
        ),
    ]
