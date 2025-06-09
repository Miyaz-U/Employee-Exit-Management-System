from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('home/', views.homepage_view, name='homepage'),
    path('signup/', views.signup_view, name='signup'),   #It defines a route that tells Django: “When the user visits this URL, run this function.”
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('profile/', views.profile_view, name='profile_view'),
    path('my_requests/', views.my_requests, name='my_requests'),
    path('submit_resignation/', views.submit_resignation, name='submit_resignation'),
    path('submit_feedback/<int:resign_id>/', views.submit_feedback, name='submit_feedback'),
    path('approval_status/<int:resign_id>/', views.approval_status, name='approval_status'),
    #path('forward/<int:resign_id>/', views.forward_to_manager, name='forward_to_manager'),
    path('hr_review/<int:resign_id>/', views.hr_review_resignation, name='hr_review_resignation'),
    path('assign_resignation/<int:resign_id>/', views.assign_resignation, name='assign_resignation'),
    #path('hr_review_resignation/<int:resign_id>/', views.hr_review_resignation, name='hr_review_resignation'), # Keep this URL
    path('update_status/<int:request_id>/', views.update_exit_status, name='update_exit_status'),
    path('update_status_fin/<int:request_id>/', views.update_exit_status_fin, name='update_exit_status_fin'),
    path('disable_email/<int:request_id>/', views.disable_email, name='disable_email'),
    path('disable_system_access/<int:request_id>/', views.disable_system_access, name='disable_system_access'),
    #path('submit-asset-return/', views.submit_asset_return, name='submit_asset_return'),
    #path('mark-security-clearance/<int:request_id>/', views.mark_security_clearance, name='mark_security_clearance'),
    path('download_exit_letter/<int:resignation_id>/', views.download_exit_letter, name='download_exit_letter'),
    path('forgot-password/', views.custom_password_reset, name='custom_password_reset'),
    path('it_approvals_mail/', views.it_approvals_mail, name='it_approvals_mail'),
    #path('it_approvals_asset/', views.it_approvals_asset, name='it_approvals_asset'),
    path('hr_approvals/', views.hr_approvals, name='hr_approvals'),
    path('manager_approvals/', views.manager_approvals, name='manager_approvals'),
    path('finance_approvals/', views.finance_approvals, name='finance_approvals'),
    path('feedback_analysis/', views.feedback_analysis, name='feedback_analysis'),
    path('manager/approved-requests/', views.manager_approved_requests, name='manager_approved_requests'),
    path('finance/approved-requests/', views.finance_approved_requests, name='finance_approved_requests'),
    path('hr/approved/', views.hr_approved_requests, name='hr_approved_requests'),
    #path('security/approvals/', views.security_view, name='security_approvals'),
    path('security/', views.security_view, name='security_view'),
    #path('security/approve/<int:resign_id>/', views.security_approve, name='security_approve'),
    path('security/approve/<int:resign_id>/', views.security_approve_asset, name='security_approve_asset'),
]
