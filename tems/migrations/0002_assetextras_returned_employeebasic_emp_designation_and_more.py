# Generated by Django 5.1.7 on 2025-05-23 06:58

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tems', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='assetextras',
            name='returned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeebasic',
            name='emp_designation',
            field=models.TextField(default='Trainee'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employeebasic',
            name='emp_join_date',
            field=models.DateField(default=datetime.date(2023, 5, 1)),
        ),
        migrations.AddField(
            model_name='employeebasic',
            name='gender',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female')], default='Male', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='feedback',
            name='sentiment',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='feedback',
            name='summary',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='feedback',
            name='topics',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='IT_spoc_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='it_spoc', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='finance_approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='finance_reviewed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='finance_spoc_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='finance_spoc', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='hr_spoc_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hr_spoc', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='manager_spoc_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manager_spoc', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='security_done',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='resignationextras',
            name='security_spoc_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='security_spoc', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='employeebasic',
            name='emp_dob',
            field=models.DateField(default=datetime.date(2000, 1, 1)),
        ),
        migrations.AlterField(
            model_name='employeebasic',
            name='emp_phn_no',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='resignation',
            name='pend_from',
            field=models.CharField(choices=[('HR', 'HR'), ('Manager', 'Manager'), ('IT', 'IT'), ('Security', 'Security'), ('Finance', 'Finance')], max_length=50),
        ),
        migrations.AlterField(
            model_name='resignation',
            name='resign_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='resignation',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], max_length=50),
        ),
        migrations.CreateModel(
            name='SecurityNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, null=True)),
                ('cleared_at', models.DateTimeField(auto_now_add=True)),
                ('cleared_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('resignation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='security_note', to='tems.resignation')),
            ],
        ),
    ]
