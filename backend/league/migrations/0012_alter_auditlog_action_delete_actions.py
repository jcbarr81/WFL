from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0011_alter_auditlog_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('league.create', 'League Created'),
                    ('league.update', 'League Updated'),
                    ('league.delete', 'League Deleted'),
                    ('team.create', 'Team Created'),
                    ('team.delete', 'Team Deleted'),
                    ('roster.add', 'Roster Add'),
                    ('roster.release', 'Roster Release'),
                    ('league.schedule.generate', 'Schedule Generated'),
                    ('trade.create', 'Trade Created'),
                    ('trade.accept', 'Trade Accepted'),
                    ('trade.reverse', 'Trade Reversed'),
                    ('waiver.release', 'Waiver Release'),
                    ('waiver.claim', 'Waiver Claim'),
                    ('contract.update', 'Contract Update'),
                    ('draft.create', 'Draft Created'),
                    ('draft.pick', 'Draft Pick Made'),
                    ('game.complete', 'Game Completed'),
                ],
            ),
        ),
    ]
