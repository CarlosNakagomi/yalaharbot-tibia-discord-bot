from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('bot', '0005_discordserversettings_watchedguild_watchedworld')]

    operations = [
        migrations.CreateModel(
            name='EnemyListConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_world', models.CharField(blank=True, max_length=50)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='EnemyGuild',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
    ]
