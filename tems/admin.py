from django.contrib import admin
from .models import Resignation, Feedback, Asset, EmployeeBasic, ResignationExtras, AssetExtras
from .forms import EmployeeBasicAdminForm

@admin.register(Resignation)
class ResignationAdmin(admin.ModelAdmin):
    list_display = ('resign_id', 'emp_code', 'res_date', 'last_day', 'reason','status', 'pend_from', 'hr_comments')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'skills', 'suggestions_role', 'culture', 'valued', 'support',
                    'leadership', 'retention', 'incidents', 'suggestions_company',
                    'recommend', 'likes', 'experience', 'feedback')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_id', 'emp_code','asset_name', 'serial_number', 'asset_allocated','asset_type','last_upd_date_time')

@admin.register(EmployeeBasic)
class EmployeeBasicAdmin(admin.ModelAdmin):
    form = EmployeeBasicAdminForm
    list_display = ('emp_code', 'emp_name', 'emp_age', 'emp_dob', 'emp_comp_email',
                    'emp_pers_email', 'emp_phn_no', 'emp_loc', 'emp_cli_name')
    readonly_fields = ('emp_age',)

@admin.register(ResignationExtras)
class ResignationExtrasAdmin(admin.ModelAdmin):
    #list_display = ('resignation', 'forwarded_to_manager','hr_reviewed','manager_reviewed','manager_approved','email_disabled','system_access_disabled','it_clearance','security_clearance','final_hr_approved','finance_clearance')
    list_display = ('resignation','hr_reviewed','manager_reviewed','manager_approved','email_disabled','system_access_disabled','it_clearance','security_clearance','final_hr_approved','finance_clearance')

@admin.register(AssetExtras)
class AssetExtrasAdmin(admin.ModelAdmin):
    list_display = ('asset', 'assigned_for_exit')




admin.site.site_header = "TechStar Administration"
admin.site.site_title = "TechStar Admin"
admin.site.index_title = ""