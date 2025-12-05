from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("league", "0019_sim_phase3"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tradeitem",
            name="player",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to="league.player"),
        ),
        migrations.AddField(
            model_name="tradeitem",
            name="cash_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="tradeitem",
            name="pick_round",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tradeitem",
            name="pick_year",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
