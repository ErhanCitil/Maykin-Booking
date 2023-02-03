# Generated by Django 4.1.5 on 2023-02-03 13:27

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0026_highlight_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='terms',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
    ]
