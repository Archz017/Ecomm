# Generated by Django 3.1.2 on 2021-11-08 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_auto_20211108_2243'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(default='-----Description-----', max_length=600),
        ),
    ]
