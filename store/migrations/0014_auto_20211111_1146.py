# Generated by Django 3.1.2 on 2021-11-11 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_product_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='is_buyer',
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.TextField(default='Util', max_length=50),
        ),
    ]
