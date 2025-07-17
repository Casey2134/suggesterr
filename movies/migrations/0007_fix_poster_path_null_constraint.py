# Generated manually to fix poster_path NOT NULL constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0006_remove_movie_available_on_jellyfin_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='poster_path',
            field=models.CharField(max_length=500, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='backdrop_path',
            field=models.CharField(max_length=500, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='imdb_id',
            field=models.CharField(max_length=20, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='original_title',
            field=models.CharField(max_length=500, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='overview',
            field=models.TextField(blank=True, null=True),
        ),
    ]