# Generated by Django 5.2.1 on 2025-06-12 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_tag_order_tags'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='tags',
        ),
        migrations.AddField(
            model_name='product',
            name='tags',
            field=models.ManyToManyField(to='account.tag'),
        ),
    ]
