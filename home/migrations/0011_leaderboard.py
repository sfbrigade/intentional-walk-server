# Generated by Django 3.2.15 on 2023-03-02 17:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_auto_20220321_0407'),
    ]

    operations = [
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('steps', models.IntegerField(help_text='Number of steps recorded')),
                ('account', models.ForeignKey(help_text='Account the data is linked to', on_delete=django.db.models.deletion.CASCADE, to='home.account')),
                ('contests', models.ForeignKey(help_text='All the contests the account is enrolled in', on_delete=django.db.models.deletion.CASCADE, to='home.contest')),
                ('device', models.ForeignKey(help_text='Device the data is coming from', on_delete=django.db.models.deletion.CASCADE, to='home.device')),
            ],
        ),
    ]
