# Generated by Django 4.2.6 on 2023-10-31 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_followerscount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.FileField(upload_to='post_images'),
        ),
    ]
