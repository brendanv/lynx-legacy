# Generated by Django 5.0 on 2024-02-01 02:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lynx', '0014_feed_auto_add_feed_items_to_library'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('content', models.TextField()),
                ('hostname', models.CharField(max_length=500)),
                ('url', models.URLField(max_length=2000)),
                ('link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='lynx.link')),
                ('tags', models.ManyToManyField(blank=True, to='lynx.tag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-saved_at'],
            },
        ),
    ]
