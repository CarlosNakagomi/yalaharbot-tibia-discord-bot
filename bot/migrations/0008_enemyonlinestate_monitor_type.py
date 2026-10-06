from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0007_enemy_observations_and_online_state'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='enemyonlinestate',
            name='unique_enemy_online_state',
        ),
        migrations.AddField(
            model_name='enemyonlinestate',
            name='monitor_type',
            field=models.CharField(default='enemy', max_length=10),
        ),
        migrations.AddConstraint(
            model_name='enemyonlinestate',
            constraint=models.UniqueConstraint(
                fields=('monitor_type', 'world_key', 'character_key'),
                name='unique_monitored_online_state',
            ),
        ),
    ]
