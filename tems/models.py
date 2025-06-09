from django.db import models
from django.contrib.auth.models import User
from datetime import date, datetime

class EmployeeBasic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employeebasic')
    emp_code = models.IntegerField(primary_key=True)
    emp_name = models.TextField()
    emp_age = models.IntegerField()
    #emp_dob = models.DateField(default='2000-01-01')
    emp_dob = models.DateField(default=date(2000, 1, 1))
    emp_comp_email = models.EmailField()
    emp_pers_email = models.EmailField()
    emp_phn_no = models.CharField(max_length=30)
    emp_loc = models.TextField()
    emp_cli_name = models.TextField()
    emp_join_date = models.DateField(default=date(2023, 5, 1))
    emp_designation = models.TextField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])
    
    def save(self, *args, **kwargs):
        # Ensure emp_dob is a date object
        if isinstance(self.emp_dob, str):
            try:
                self.emp_dob = datetime.strptime(self.emp_dob, "%Y-%m-%d").date()
            except ValueError:
                self.emp_dob = None

        # Calculate age from emp_dob if available
        if self.emp_dob:
            today = date.today()
            self.emp_age = today.year - self.emp_dob.year - ((today.month, today.day) < (self.emp_dob.month, self.emp_dob.day))
        else:
            self.emp_age = 0  # Default to 0 if dob is invalid/missing

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.emp_code} - {self.emp_name}"


class Resignation(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    PENDING_FROM_CHOICES = [
        ('HR', 'HR'),
        ('Manager', 'Manager'),
        ('IT', 'IT'),
        ('Security', 'Security'),
        ('Finance', 'Finance'),
    ]
    resign_id = models.AutoField(primary_key=True)
    emp_code = models.ForeignKey(EmployeeBasic, on_delete=models.CASCADE)
    res_date = models.DateField()
    last_day = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    pend_from = models.CharField(max_length=50, choices=PENDING_FROM_CHOICES)
    hr_comments = models.TextField()
    manager_comments = models.TextField()
    finance_comments = models.TextField()

    def __str__(self):
        return f"Resignation {self.resign_id} - {self.emp_code.emp_name}"


    def __str__(self):
        return f"{self.resign_id} - {self.emp_code.emp_code} - {self.emp_code.emp_name}"



# Feedback model to store feedback form data
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resign_id = models.ForeignKey(Resignation, on_delete=models.CASCADE)
    skills = models.TextField()
    suggestions_role = models.TextField()
    culture = models.TextField()
    valued = models.TextField()
    support = models.TextField()
    leadership = models.IntegerField()
    retention = models.TextField()
    incidents = models.TextField()
    suggestions_company = models.TextField()
    recommend = models.CharField(max_length=3)
    likes = models.TextField()
    experience = models.IntegerField()
    feedback = models.TextField()
    sentiment = models.CharField(max_length=10, null=True, blank=True)  # e.g., Positive, Negative, Mixed
    topics = models.TextField(null=True, blank=True)  # e.g., comma-separated "Speed, Process"
    summary = models.TextField(null=True, blank=True)  # e.g

    def __str__(self):
        return f"Feedback from {self.id}"
    
class Asset(models.Model):
    ASSET_TYPES = [
        ('Laptop', 'Laptop'),
        ('Mobile', 'Mobile'),
        ('Tablet', 'Tablet'),
        ('Desktop', 'Desktop'),
        ('Other', 'Other'),
    ]
    
    asset_id = models.IntegerField(primary_key=True)
    emp_code = models.ForeignKey(EmployeeBasic, on_delete=models.CASCADE)
    asset_name = models.TextField()
    serial_number = models.TextField()
    asset_allocated = models.BooleanField()
    asset_type = models.TextField(choices=ASSET_TYPES)
    last_upd_date_time = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.asset_id} - {self.asset_name}"
    
class ResignationExtras(models.Model):
    resignation = models.OneToOneField(Resignation, on_delete=models.CASCADE, related_name='extras')

    #forwarded_to_manager = models.BooleanField(default=False)
    hr_reviewed = models.BooleanField(default=False)
    manager_reviewed = models.BooleanField(default=False)
    manager_approved = models.BooleanField(default=False)
    finance_reviewed = models.BooleanField(default=False)
    finance_approved = models.BooleanField(default=False)
    email_disabled = models.BooleanField(default=False)
    system_access_disabled = models.BooleanField(default=False)
    it_clearance = models.BooleanField(default=False)
    security_clearance = models.BooleanField(default=False)
    security_done = models.BooleanField(default=False)
    final_hr_approved = models.BooleanField(default=False)
    finance_clearance = models.BooleanField(default=False)
    hr_spoc_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_spoc')
    manager_spoc_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_spoc')
    IT_spoc_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='it_spoc') # Corrected related name
    finance_spoc_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_spoc')
    security_spoc_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_spoc')
    rejected_by = models.CharField(max_length=20, null=True, blank=True)  # values: "Manager", "HR", "Finance"
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    final_pay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f"Extras for resignation {self.resignation.resign_id}"
    
class AssetExtras(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='extras')
    assigned_for_exit = models.ForeignKey(
        Resignation, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assets_for_exit'
    )
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"Extras for Asset {self.asset.asset_id}"
# Create your models here.


class SecurityNote(models.Model):
    resignation = models.OneToOneField(Resignation, on_delete=models.CASCADE, related_name='security_note')
    note = models.TextField(blank=True, null=True)
    cleared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cleared_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Security Note for {self.resignation.resign_id}"
