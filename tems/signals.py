from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import EmployeeBasic



@receiver(post_save, sender=User)
def create_employee_basic(sender, instance, created, **kwargs):
    if created:
        EmployeeBasic.objects.create(
            user=instance,
            emp_code=instance.id,  # or another unique ID
            emp_name=instance.get_full_name() or instance.username,
            emp_age=25,  # placeholder
            emp_dob='2000-01-01',  # placeholder
            emp_comp_email=f'{instance.username}@example.com',
            emp_pers_email='user@example.com',
            emp_phn_no=9999999999,
            emp_loc='Unknown',
            emp_cli_name='Unknown'
        )