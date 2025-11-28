from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('league', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='league.league')),
            ],
            options={
                'unique_together': {('league', 'year')},
            },
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('is_playoffs', models.BooleanField(default=False)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weeks', to='league.season')),
            ],
            options={
                'unique_together': {('season', 'number', 'is_playoffs')},
                'ordering': ['season_id', 'number'],
            },
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_score', models.IntegerField(default=0)),
                ('away_score', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('in_progress', 'In Progress')], default='scheduled', max_length=20)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('week', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='games', to='league.week')),
                ('home_team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='home_games', to='league.team')),
                ('away_team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='away_games', to='league.team')),
            ],
            options={
                'ordering': ['week_id', 'id'],
            },
        ),
    ]
