from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0006_enemylistconfiguration_enemyguild'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnemyObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('character_name', models.CharField(max_length=100)),
                ('character_key', models.CharField(max_length=100, unique=True)),
                ('observation', models.TextField(max_length=2000)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['character_name']},
        ),
        migrations.CreateModel(
            name='EnemyOnlineState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('world', models.CharField(max_length=50)),
                ('world_key', models.CharField(max_length=50)),
                ('character_name', models.CharField(max_length=100)),
                ('character_key', models.CharField(max_length=100)),
                ('is_online', models.BooleanField(default=False)),
                ('session_started_at', models.DateTimeField(blank=True, null=True)),
                ('last_observed_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='enemyonlinestate',
            constraint=models.UniqueConstraint(fields=('world_key', 'character_key'), name='unique_enemy_online_state'),
        ),
    ]
