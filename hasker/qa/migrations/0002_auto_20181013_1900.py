# Generated by Django 2.1.2 on 2018-10-13 19:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('qa', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisLikeAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DisLikeQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LikeAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LikeQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='answer',
            name='rating',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='question',
            name='rating',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='likequestion',
            name='like_question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ques_likes', to='qa.Question'),
        ),
        migrations.AddField(
            model_name='likequestion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='likeanswer',
            name='like_answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ans_likes', to='qa.Question'),
        ),
        migrations.AddField(
            model_name='likeanswer',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dislikequestion',
            name='dislike_question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ques_dislikes', to='qa.Question'),
        ),
        migrations.AddField(
            model_name='dislikequestion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dislikeanswer',
            name='dislike_answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ans_dislikes', to='qa.Question'),
        ),
        migrations.AddField(
            model_name='dislikeanswer',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
