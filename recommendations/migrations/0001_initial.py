# Generated by Django 4.2.7 on 2025-07-16 23:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNegativeFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField()),
                ('content_type', models.CharField(choices=[('movie', 'Movie'), ('tv', 'TV Show')], max_length=10)),
                ('reason', models.CharField(choices=[('not_interested', 'Not Interested'), ('already_seen', 'Already Seen'), ('not_my_genre', 'Not My Genre'), ('poor_rating', 'Poor Rating')], default='not_interested', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'content_type'], name='recommendat_user_id_0dc19b_idx'), models.Index(fields=['tmdb_id', 'content_type'], name='recommendat_tmdb_id_ca7bfb_idx')],
                'unique_together': {('user', 'tmdb_id', 'content_type')},
            },
        ),
    ]
