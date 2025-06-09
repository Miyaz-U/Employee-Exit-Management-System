from typing import cast
from . import models
from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from .models import Resignation, Feedback, Asset, EmployeeBasic, ResignationExtras, AssetExtras, SecurityNote
from django.http import HttpResponse
from .forms import ResignForm, FeedbackForm, CustomUserCreationForm, AssignResignationForm
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import requests
from io import BytesIO
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.timezone import now
from . import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from textblob import TextBlob
import re
from google import genai
#import google.generativeai as genai
#import os

def paginate_queryset(request, queryset, per_page=6):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    return items


@never_cache
@login_required
def homepage_view(request):
    user_groups = list(request.user.groups.values_list('name', flat=True))
    context = {'user': request.user,'user_groups': user_groups,}
    if 'hr' in user_groups:
        #resignations = Resignation.objects.all().select_related('extras')
        resignations = Resignation.objects.filter(
        extras__hr_spoc_id__isnull=True
    ).exclude(emp_code__user=request.user) | Resignation.objects.filter(
        extras__hr_spoc_id=request.user
    ).select_related('extras')
        paginated_resignations = paginate_queryset(request, resignations, per_page=6)
        context['resignations'] = paginated_resignations
     # 👇 Manager data must go to 'exit_requests' and 'pending_count'
    if 'manager' in user_groups:
        #exit_requests = Resignation.objects.filter(extras__forwarded_to_manager=True, extras__manager_reviewed=False, extras__manager_spoc_id=request.user)
        exit_requests = Resignation.objects.filter(extras__manager_reviewed=False, extras__manager_spoc_id=request.user)
        paginated_resignations = paginate_queryset(request, exit_requests, per_page=6)
        context['exit_requests'] = paginated_resignations
        context['pending_count'] = exit_requests.count()
    # 👇 IT Admin data must go to 'exit_requests' and 'pending_count
    if 'it' in user_groups:
        it_exit_requests = Resignation.objects.filter(extras__manager_reviewed=True, extras__manager_approved=True, extras__IT_spoc_id=request.user).select_related('extras').prefetch_related('assets_for_exit__asset')
        paginated_resignations = paginate_queryset(request, it_exit_requests, per_page=6)
        context['it_exit_requests'] = paginated_resignations
    if 'finance' in user_groups:
        exit_requests = Resignation.objects.filter(extras__it_clearance=True, extras__finance_reviewed=False, extras__finance_spoc_id=request.user)
        paginated_resignations = paginate_queryset(request, exit_requests, per_page=6)
        context['exit_requests'] = paginated_resignations
        context['pending_count'] = exit_requests.count()
    return render(request, 'homepage.html', context)


def signup_view(request: HttpRequest):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # Redirect to login page after successful signup
        else:
            print(form.errors)
    else:
        form = CustomUserCreationForm()
    
    return render(request, "signup.html", {"form": form})

def login_view(request: HttpRequest):
    if request.method == 'POST':
        #request.method tells you which HTTP method was used for the request:

#"GET" – usually means the user is visiting the page.

#"POST" – usually means the user submitted a form.
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            return redirect('homepage')  # default fallback
        else:
            return render(request, 'login.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

@never_cache
def logout_view(request: HttpRequest):
    logout(request)
    return redirect('login')


@never_cache
@login_required
def my_requests(request: HttpRequest):
    user = request.user
    # Fetch all resignations submitted by this user
    employee_basic = cast(EmployeeBasic, request.user.employeebasic)
    emp_code = employee_basic.emp_code
    employee = get_object_or_404(EmployeeBasic, emp_code=emp_code)
    resignation = Resignation.objects.filter(emp_code=employee).order_by('-resign_id')

    # For each resignation, determine where it is stuck (pending with whom)
    requests_with_stage = []
    for resignation in resignation:
        extras, _ = ResignationExtras.objects.get_or_create(resignation=resignation)
        '''if not extras.forwarded_to_manager:
            stage = "Forwarded to HR"'''
        '''elif extras.forwarded_to_manager and not extras.manager_reviewed:
            stage = "Pending with Manager"'''
        if resignation.status == "Rejected":
            stage = f"Rejected by {extras.rejected_by}" if extras.rejected_by else "Rejected"
        elif not extras.hr_reviewed:
            stage = "Pending with HR and Manager"
        elif not extras.manager_reviewed:
            stage = "Pending with HR and Manager"
        elif not extras.security_clearance:
            stage = "Pending with Security"
        elif not extras.finance_reviewed:
            stage = "Pending with Finance"
        elif not extras.it_clearance:
            stage = "Pending with IT Department"
        elif not extras.final_hr_approved and all([
            extras.manager_reviewed,
            extras.it_clearance,
            extras.security_clearance,
            extras.finance_reviewed
            ]):
            stage = "Pending Final HR Approval"
        elif resignation.status == "Approved":
            stage = "Exit Completed"
        else:
            stage = "Unknown"


        requests_with_stage.append({
            'resignation': resignation,
            'extras': extras,
            'stage': stage
        })

    paginated_requests = paginate_queryset(request, requests_with_stage, per_page=6)
    return render(request, 'my_requests.html', {
        'requests_with_stage': paginated_requests
    })


# Handle resignation form submission
@never_cache
@login_required
def submit_resignation(request: HttpRequest):   
    if request.method == 'POST':
        print("Raw POST data:", request.POST)  # Debugging
        form = ResignForm(request.POST)
        if form.is_valid():
            resignation = form.save(commit=False)  # Save the form but don't commit to DB yet
            resignation.emp_code = request.user.employeebasic  # Assuming OneToOne between User & EmployeeBasic
            resignation.res_date = now().date()
            resignation.last_day = resignation.res_date + timedelta(days=60)  # Placeholder: Calculate based on notice period
            resignation.status = 'Pending'
            resignation.pend_from = 'HR'
            resignation.hr_comments = ''
            resignation.manager_comments = ''
            resignation.finance_comments = ''
            print("Before save: ", resignation.reason, resignation.emp_code)
            resignation.save()
            print("dfghj",resignation.resign_id)
            return redirect('submit_feedback', resign_id=resignation.resign_id)
        else:
            print(form.errors)
            # Handle form errors here if needed
    else:
                form = ResignForm()
    return render(request, 'ResignationForm.html', {'form': form})



# Handle feedback form submission
'''@never_cache
@login_required
def submit_feedback(request: HttpRequest, resign_id: int):
    resignation = get_object_or_404(Resignation, resign_id=resign_id)
    print(request.method)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            print("Valid Form Data:", form.cleaned_data)
            feedback = form.save(commit=False)  # Save the form but don't commit to DB yet
            # Get the most recent resignation (assuming 1-to-1 per session)
            feedback.user = request.user
            feedback.resign_id = resignation
            feedback.save()

            subject = f'Resignation Submitted - {request.user.username}'
            message =  message=f"Dear {request.user.first_name}, We have received your resignation request submitted through the Employee Exit Management System. Your request has been forwarded to the necessary departments for processing. You will be notified as each stage of the clearance and approval process is completed. If you have any questions or need to make updates, please contact HR"
            recipient_list = ['sreenathnaidu2002@gmail.com']  # Replace with actual HR email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            return JsonResponse({'success': True, 'message': 'Form has been submitted successfully', 'redirect_url': '/my_requests/'})

        else:
            print(form.errors)
            # Prepare errors for JSON response
            errors = {}
            for field, error in form.errors.items():
                errors[field] = error.as_text()  # Or error.as_json() for a different format
            return JsonResponse({'success': False, 'message': 'Form submission failed. Please check your inputs.', 'errors': errors}, status=400)  # Return 400 for bad request
    else:
        form = FeedbackForm()
        print("Received GET request instead of POST")
        return render(request, 'FeedbackPage.html', {'form': form,'resignation': resignation})'''


@never_cache
@login_required
def submit_feedback(request: HttpRequest, resign_id: int):
    resignation = get_object_or_404(Resignation, resign_id=resign_id)
    extras, created = ResignationExtras.objects.get_or_create(resignation=resignation)
    print(request.method)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.resign_id = resignation
            # Perform full analysis
            sentiment, topics, summary = analyze_feedback_text(feedback.feedback)
            feedback.sentiment = sentiment
            feedback.topics = ', '.join(topics)
            feedback.summary = summary
            feedback.save()

            '''# Automatically forward to both HR and Manager
            extras.forwarded_to_manager = True
            extras.hr_reviewed = True  # You can remove this if HR should still take action later
            extras.save()
            resignation.status = "Forwarded to Manager"
            resignation.save()'''
            
            # Notify Manager
            if extras.manager_spoc_id:
                manager_email = EmployeeBasic.objects.get(user=extras.manager_spoc_id).emp_pers_email
                send_mail(
                    subject=f'Resignation Submitted - {request.user.username}',
                    message=f"Dear Manager, {request.user.first_name} has submitted their resignation. Please review the request in the Exit Management System.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[manager_email],
                )


            # Mail to employee
            subject = f'Resignation Submitted - {request.user.username}'
            message =  message=f"Dear {request.user.first_name}, We have received your resignation request submitted through the Employee Exit Management System. Your request has been forwarded to the necessary departments for processing. You will be notified as each stage of the clearance and approval process is completed. If you have any questions or need to make updates, please contact HR"
            recipient_list = [resignation.emp_code.emp_pers_email]  # Replace with actual employee email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            # Mail to HR
            subject = f'Employee Resignation Notification - {request.user.username}'
            message =  message=f"Dear HR, {request.user.first_name} has submitted a resignation request through the Employee Exit Management System. Please review and process the request at your earliest convenience."
            hr_group = Group.objects.get(name='hr')
            hr_users = hr_group.user_set.all()
            recipient_list = [EmployeeBasic.objects.get(user=u).emp_pers_email for u in hr_users]  # Replace with actual HR email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            # Mail to manager
            subject = f'Employee Resignation - {resignation.emp_code.emp_name}'
            message = f"Dear manager, Please be informed that {resignation.emp_code.emp_name} has submitted their resignation. Please begin the necessary handover and offboarding procedures for your team."
            manager_user = extras.manager_spoc_id
            if manager_user:
                manager_email = EmployeeBasic.objects.get(user=manager_user).emp_pers_email
                recipient_list = [manager_email] # Replace with actual manager email
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            return JsonResponse({'success': True, 'message': 'Form has been submitted successfully', 'redirect_url': '/my_requests/'})

        else:
            print(form.errors)
            # Prepare errors for JSON response
            errors = {}
            for field, error in form.errors.items():
                errors[field] = error.as_text()  # Or error.as_json() for a different format
            return JsonResponse({'success': False, 'message': 'Form submission failed. Please check your inputs.', 'errors': errors}, status=400)  # Return 400 for bad request
    else:
        form = FeedbackForm()
        print("Received GET request instead of POST")
        return render(request, 'FeedbackPage.html', {'form': form,'resignation': resignation})
# Create your views here.

'''@never_cache
@login_required
def forward_to_manager(request: HttpRequest, resign_id):
    resignation = get_object_or_404(Resignation, pk=resign_id)
    extras, created = ResignationExtras.objects.get_or_create(resignation=resignation)
    extras.forwarded_to_manager = True
    extras.hr_reviewed = True  # Mark HR as reviewed when forwarding to manager
    extras.save()
    resignation.status = "Forwarded to Manager"
    resignation.save()
    return redirect('profile_view')  # Redirect to the profile page or any other page you want

@never_cache
@login_required
def forward_to_manager(request: HttpRequest, resign_id):
    resignation = get_object_or_404(Resignation, pk=resign_id)
    extras, created = ResignationExtras.objects.get_or_create(resignation=resignation)
    extras.forwarded_to_manager = True
    extras.hr_reviewed = True  # Mark HR as reviewed when forwarding to manager
    extras.save()
    resignation.status = "Forwarded to Manager"
    resignation.save()
    # Mail to employee
    subject = f'Update on your resignation - {resignation.emp_code.emp_name}'
    message = f"Dear {resignation.emp_code.emp_name}, Your resignation request has been forwarded to the manager for review. You will be notified once the manager has reviewed your request."
    recipient_list = [resignation.emp_code.emp_pers_email]  # Replace with actual employee email
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    # Mail to manager
    subject = f'Employee Resignation - {request.user.username}'
    message = f"Dear manager, Please be informed that {resignation.emp_code.emp_name} has submitted their resignation. Please begin the necessary handover and offboarding procedures for your team."
    manager_user = extras.manager_spoc_id
    if manager_user:
        manager_email = EmployeeBasic.objects.get(user=manager_user).emp_pers_email
    recipient_list = [manager_email]

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    return redirect('profile_view')  # Redirect to the profile page or any other page you want'''


@never_cache
@login_required
def assign_resignation(request, resign_id):
    resignation = get_object_or_404(Resignation, resign_id=resign_id)
    extras, created = ResignationExtras.objects.get_or_create(resignation=resignation)

    # If assignment is already done, redirect to the review page
    if extras.hr_spoc_id:
        return redirect('hr_review_resignation', resign_id=resign_id)

    if request.method == 'POST':
        form = AssignResignationForm(request.POST, instance=extras)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.hr_spoc_id = request.user  # Assign current HR user
            assignment.save()
            return redirect('hr_review_resignation', resign_id=resign_id)
    else:
        form = AssignResignationForm(instance=extras)

    return render(request, 'assign_resignation.html', {'form': form, 'resignation': resignation})


@never_cache
@login_required
def hr_review_resignation(request, resign_id):
    resignation = get_object_or_404(Resignation, resign_id=resign_id)
    extras, _ = ResignationExtras.objects.get_or_create(resignation=resignation)

    # Check if the current user is the assigned HR SPOC
    if extras.hr_spoc_id != request.user:
        return HttpResponseForbidden("You are not authorized to view this resignation.")

    manager_done = extras.manager_reviewed
    it_done = (
        extras.email_disabled and
        extras.system_access_disabled and
        extras.it_clearance
    )
    finance_done = extras.finance_reviewed
    security_done = extras.security_clearance # Check for security clearance

    # Create a dynamic list of missing clearances
    pending_clearances = []
    if not manager_done:
        pending_clearances.append("Manager")
    if not it_done:
        pending_clearances.append("IT")
    if not security_done:
        pending_clearances.append("Security")
    if not finance_done:
        pending_clearances.append("Finance")


    if request.method == 'POST':
        resignation.hr_comments = request.POST.get('hr_comments', '')

        '''if 'forward' in request.POST:
            extras.forwarded_to_manager = True
            resignation.status = "Forwarded to Manager"
            resignation.save()
            extras.save()
            # Mail to employee
            subject = f'Update on your resignation - {resignation.emp_code.emp_name}'
            message = f"Dear {resignation.emp_code.emp_name}, Your resignation request has been forwarded to the manager for review. You will be notified once the manager has reviewed your request."
            recipient_list = [resignation.emp_code.emp_pers_email]  # Replace with actual employee email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            # Mail to manager
            subject = f'Employee Resignation - {resignation.emp_code.emp_name}'
            message = f"Dear manager, Please be informed that {resignation.emp_code.emp_name} has submitted their resignation. Please begin the necessary handover and offboarding procedures for your team."
            manager_user = extras.manager_spoc_id
            if manager_user:
                manager_email = EmployeeBasic.objects.get(user=manager_user).emp_pers_email
            recipient_list = [manager_email] # Replace with actual manager email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
            return render(request, 'hr_review_resignation.html', {
                'resignation': resignation,
                'manager_done': manager_done,
                'it_done': it_done,
                'finance_done': finance_done,
                'security_done': security_done, # Pass security_done to template
                'forward_success': True
            })# Changed to profile_view'''
        
        if 'forward' in request.POST:
            resignation.hr_comments = request.POST.get('hr_comments', '')
            resignation.save()
            extras.hr_reviewed = True
            extras.save()
            
            return render(request, 'hr_review_resignation.html', {
                'resignation': resignation,
                'manager_done': manager_done,
                'it_done': it_done,
                'finance_done': finance_done,
                'security_done': security_done,
                'submitted': True,
                'action_success': True,
                'message': "HR comments submitted.",
                'pending_clearances': pending_clearances,
            })

        if 'forward-btn' in request.POST:
            if not manager_done or not it_done or not finance_done or not security_done: # Include security_done in checks
                error_msg = "Final HR decision requires:"
                if not manager_done:
                    error_msg += " Manager approval;"
                if not it_done:
                    error_msg += " Full IT + Security clearance;"
                if not finance_done:
                    error_msg += " Finance clearance;"
                if not security_done: # Add security clearance error message
                    error_msg += " Security clearance;"
                return render(request, 'hr_review_resignation.html', {
                    'resignation': resignation,
                    'manager_done': manager_done,
                    'it_done': it_done,
                    'finance_done': finance_done,
                    'security_done': security_done, # Pass security_done to template
                    'error': error_msg,
                    'pending_clearances': pending_clearances,
                })

            decision = request.POST.get('hr_decision')
            if decision == 'approve':
                resignation.status = 'Approved'
                extras.final_hr_approved = True
                extras.hr_reviewed = True
                message = "Resignation approved successfully."
                # Mail to employee
                subject = f' Update on Your Resignation - {resignation.emp_code.emp_name}'
                messagemail = f"Dear {resignation.emp_code.emp_name}, Your resignation request has been approved by the HR department. You can now download your relieving letter."
                recipient_list = [resignation.emp_code.emp_pers_email]  # Replace with actual employee email
                send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
            elif decision == 'reject':
                resignation.status = 'Rejected'
                extras.hr_reviewed = True
                extras.final_hr_approved = False  # explicitly mark HR rejection
                extras.rejected_by = "HR"
                extras.save()
                message = "Resignation rejected."
                # Mail to employee
                subject = f'Update on your resignation - {resignation.emp_code.emp_name}'
                messagemail = f"Dear {resignation.emp_code.emp_name}, Your resignation request has been rejected by the HR department. Please contact HR for further assistance."
                recipient_list = [resignation.emp_code.emp_pers_email] # Replace with actual employee email
                send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
            resignation.save()
            extras.save()
            return render(request, 'hr_review_resignation.html', {
                'resignation': resignation,
                'manager_done': manager_done,
                'it_done': it_done,
                'finance_done': finance_done,
                'security_done': security_done, # Pass security_done to template
                'submitted': True,
                'action_success': True,
                'message': message,
                'pending_clearances': pending_clearances,
            })

    return render(request, 'hr_review_resignation.html', {
        'resignation': resignation,
        'manager_done': manager_done,
        'it_done': it_done,
        'finance_done': finance_done,
        'security_done': security_done, # Pass security_done to template
        'submitted': extras.hr_reviewed,
        'pending_clearances': pending_clearances,
    })

@never_cache
@login_required
def approval_status(request: HttpRequest, resign_id: int):
    employee = get_object_or_404(EmployeeBasic, emp_code=request.user.employeebasic.emp_code)
    if resign_id:
        resignation = get_object_or_404(Resignation, resign_id=resign_id, emp_code=employee)
    else:
        resignation = Resignation.objects.filter(emp_code=employee).order_by('-resign_id').first()

    if not resignation:
        return render(request, 'ApprovalStatusEmployee.html', {
            'no_resignation': True
        })
    extras, _ = ResignationExtras.objects.get_or_create(resignation=resignation)
    manager_done = extras.manager_reviewed
    it_done = (
        extras.email_disabled and
        extras.system_access_disabled and
        extras.it_clearance
        #extras.security_clearance
    )
    hr_done = extras.hr_reviewed and extras.final_hr_approved
    finance_done = extras.finance_reviewed
    security_done = extras.security_clearance # Check for security clearance


    return render(request, 'ApprovalStatusEmployee.html', {
        'resignation': resignation,
        'manager_done': manager_done,
        'it_done': it_done,
        'hr_done': hr_done,
        'finance_done':finance_done,
        'security_done': security_done, # Pass security_done to template
    })


@never_cache
@login_required
def download_exit_letter(request, resignation_id):
    resignation = get_object_or_404(Resignation, resign_id=resignation_id)
    extras, _ = ResignationExtras.objects.get_or_create(resignation=resignation)

    if resignation.status != 'Approved':
        return HttpResponse("Exit letter is not available until final HR approval.", status=403)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4


    banner_height = 0 
    # Load logo (use your actual path to the logo)
    # Logo from internet
    # # Use a reliable local image path
    logo_path = r"C:\myapp_static\images\techstar_logo.png"
    try:
        logo = ImageReader(logo_path)
        banner_height = 80  # Adjust size
        p.drawImage(logo, 0, height - banner_height, width=width, height=banner_height, mask='auto')
    except Exception as e:
        print(f"Logo could not be loaded: {e}")

    
    y = height - banner_height - 40

    # --- Title: Experience Letter (Centered) ---
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, "Experience Letter")

    y -= 30

    # --- Date: top-right corner ---
    p.setFont("Helvetica", 11)
    today = datetime.today().strftime("%d-%m-%Y")
    p.drawRightString(width - 40, y, f"Date: {today}")

    y -= 50

    # Content
    p.setFont("Helvetica", 12)
    line_spacing = 22

    gender = resignation.emp_code.gender.lower()
    if gender == 'male':
        subject_pronoun = "he"
        object_pronoun = "him"
        possessive_pronoun = "his"
        prefix = "Mr."
    else:
        subject_pronoun = "she"
        object_pronoun = "her"
        possessive_pronoun = "her"
        prefix = "Ms."
    
    content_lines = [
        "TO WHOMSOEVER IT MAY CONCERN",
        "",   
        f"This is to certify that {prefix} {resignation.emp_code.emp_name}, Employee code {resignation.emp_code.emp_code} is an employee",
        f"of Techstar Software Development India Pvt Limited from {resignation.emp_code.emp_join_date.strftime('%d-%m-%Y')} till {resignation.last_day.strftime('%d-%m-%Y')}.",
        f"As per our records, {possessive_pronoun} last designation at the time of offboarding from the company",
        f"was {resignation.emp_code.emp_designation}.",
        "",
        f"We wish {resignation.emp_code.emp_name} all the best in {possessive_pronoun} future endeavors.",
        "",
        "Sincerely,",
        "HR Department",
        "Techstar Software Development India Pvt Limited"
    ]

    line_height = 22
    content_block_height = len(content_lines) * line_height
    start_y = (height - banner_height - content_block_height) / 2 + content_block_height

    # --- Draw each line ---
    for idx, line in enumerate(content_lines):
        y = start_y - (idx * line_height)
        
        if line.strip() == "TO WHOMSOEVER IT MAY CONCERN":
            p.setFont("Helvetica-Bold", 12)
            p.drawCentredString(width / 2, y, line)
            underline_width = p.stringWidth(line, "Helvetica-Bold", 12)
            p.line((width - underline_width) / 2, y - 2, (width + underline_width) / 2, y - 2)
        elif line.startswith("This is to certify"):
            p.setFont("Helvetica", 12)
            text_start = 60
            static_text = f"This is to certify that {prefix} "
            p.drawString(text_start, y, static_text)
            dynamic_text = f"{resignation.emp_code.emp_name}"
            p.setFont("Helvetica-Bold", 12)
            offset = text_start + p.stringWidth(static_text, "Helvetica", 12)
            p.drawString(offset, y, dynamic_text)
            
            # Continue with: , Employee code ...
            p.setFont("Helvetica", 12)
            static2 = ", Employee code "
            offset += p.stringWidth(dynamic_text, "Helvetica-Bold", 12)
            p.drawString(offset, y, static2)
            
            dynamic2 = f"{resignation.emp_code.emp_code}"
            p.setFont("Helvetica-Bold", 12)
            offset += p.stringWidth(static2, "Helvetica", 12)
            p.drawString(offset, y, dynamic2)
            
            p.setFont("Helvetica", 12)
            end_text = " is an employee"
            offset += p.stringWidth(dynamic2, "Helvetica-Bold", 12)
            p.drawString(offset, y, end_text)

        elif line.startswith("of Techstar"):
            p.setFont("Helvetica", 12)
            text_start = 60
            static = "of Techstar Software Development India Pvt Limited from "
            p.drawString(text_start, y, static)
            
            dynamic = resignation.emp_code.emp_join_date.strftime('%d-%m-%Y')
            p.setFont("Helvetica-Bold", 12)
            offset = text_start + p.stringWidth(static, "Helvetica", 12)
            p.drawString(offset, y, dynamic)
            
            p.setFont("Helvetica", 12)
            mid = " till "
            offset += p.stringWidth(dynamic, "Helvetica-Bold", 12)
            p.drawString(offset, y, mid)
            
            dynamic2 = resignation.last_day.strftime('%d-%m-%Y')
            p.setFont("Helvetica-Bold", 12)
            offset += p.stringWidth(mid, "Helvetica", 12)
            p.drawString(offset, y, dynamic2)
            
            p.setFont("Helvetica", 12)
            
        elif "designation at the time" in line:
            p.setFont("Helvetica", 12)
            text_start = 60
            static = f"As per our records, {possessive_pronoun} last designation at the time of offboarding from the company"
            p.drawString(text_start, y, static)

        elif line.startswith("was"):
            p.setFont("Helvetica", 12)
            text_start = 60
            p.drawString(text_start, y, "was ")
            
            dynamic = resignation.emp_code.emp_designation
            p.setFont("Helvetica-Bold", 12)
            offset = text_start + p.stringWidth("was ", "Helvetica", 12)
            p.drawString(offset, y, dynamic)
            
            # Add the period after the bold designation
            p.setFont("Helvetica", 12)
            offset += p.stringWidth(dynamic, "Helvetica-Bold", 12)
            p.drawString(offset, y, ".")
            
        elif line.startswith("We wish"):
            p.setFont("Helvetica", 12)
            text_start = 60
            static = f"We wish "
            p.drawString(text_start, y, static)
            
            dynamic = resignation.emp_code.emp_name
            p.setFont("Helvetica-Bold", 12)
            offset = text_start + p.stringWidth(static, "Helvetica", 12)
            p.drawString(offset, y, dynamic)
            
            p.setFont("Helvetica", 12)
            ending = f" all the best in {possessive_pronoun} future endeavors."
            offset += p.stringWidth(dynamic, "Helvetica-Bold", 12)
            p.drawString(offset, y, ending)
            
        else:
            p.setFont("Helvetica", 12)
            p.drawString(60, y, line)
    
    

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@never_cache
@login_required
def update_exit_status(request: HttpRequest, request_id):
    exit_request = get_object_or_404(Resignation, resign_id=request_id)
    extras, created = ResignationExtras.objects.get_or_create(resignation=exit_request)
    if extras.manager_spoc_id != request.user:
        return HttpResponseForbidden("You are not authorized to review this resignation.")
    if request.method == 'POST':
        status = request.POST.get('status')
        exit_request.manager_comments = request.POST.get('manager_comments', '')
        if status == 'Approved':
            extras.manager_reviewed = True
            extras.manager_approved = True
            exit_request.status = 'Approved'
            message = "Resignation approved successfully"
            # Mail to employee
            subject = f' Update on Your Resignation - {exit_request.emp_code.emp_name}'
            messagemail = f"Dear {exit_request.emp_code.emp_name}, Your resignation request has been approved by the manager and forwarded to the IT and security for review. You will be notified once the IT disables your email and system access and security verifies your asset return."
            recipient_list = [exit_request.emp_code.emp_pers_email]  # Replace with actual employee email
            send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
            # Mail to IT and security
            subject = f'Resignation Submitted - {exit_request.emp_code.emp_name}'
            messagemail = f"Dear IT and security, This notification confirms the approved resignation of {exit_request.emp_code.emp_name}. Please proceed with disabling all system access and retrieving company assets on or before this date."
            it_user = extras.IT_spoc_id
            if it_user:
                it_email = EmployeeBasic.objects.get(user=it_user).emp_pers_email
            recipient_list = [it_email]  # Replace with actual IT and security email
            send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
        elif status == 'Rejected':
            extras.manager_reviewed = True
            extras.manager_approved = False
            extras.rejected_by = "Manager"
            extras.save()
            exit_request.status = 'Rejected'
            message = "Resignation rejected"
            # Mail to employee
            subject = f'Update on your resignation - {exit_request.emp_code.emp_name}'
            messagemail = f"Dear {exit_request.emp_code.emp_name}, Your resignation request has been rejected by the manager. Please contact HR for further assistance."
            recipient_list = [exit_request.emp_code.emp_pers_email]  # Replace with actual employee email
            send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
        exit_request.save()
        extras.save()
        return render(request, 'update_exit_status.html', {'exit_request': exit_request, 'action_success':True, 'message':message})
    return render(request, 'update_exit_status.html', {'exit_request': exit_request})


@never_cache
@login_required
def update_exit_status_fin(request: HttpRequest, request_id):
    exit_request = get_object_or_404(Resignation, resign_id=request_id)
    extras, created = ResignationExtras.objects.get_or_create(resignation=exit_request)
    if extras.finance_spoc_id != request.user:
        return HttpResponseForbidden("You are not authorized to review this resignation.")
    if request.method == 'POST':
        status = request.POST.get('status')
        exit_request.finance_comments = request.POST.get('finance_comments', '')
        exit_request.loan_amount = request.POST.get('loan_amount')
        exit_request.final_pay = request.POST.get('final_pay')

        # Update finance values
        try:
            extras.loan_amount = float(exit_request.loan_amount) if exit_request.loan_amount else None
        except ValueError:
            extras.loan_amount = None

        try:
            extras.final_pay = float(exit_request.final_pay) if exit_request.final_pay else None
        except ValueError:
            extras.final_pay = None

        if status == 'Approved':
            extras.finance_reviewed = True
            extras.finance_approved = True
            # exit_request.status = 'Approved' # Status should not be set to Approved here, it moves to Security
            # Instead, redirect to security_view or mark as pending for security
            exit_request.pend_from = 'Security' # Mark as pending for Security
            message = 'Resignation approved successfully and forwarded to Security.'
            exit_request.save()
            extras.save()
            # Mail to employee
            subject = f'Update on Your Resignation - {exit_request.emp_code.emp_name}'
            messagemail = f"Dear {exit_request.emp_code.emp_name}, Your resignation has been fully approved and all offboarding procedures are complete. You will receive your official relieving letter shortly."
            recipient_list = [exit_request.emp_code.emp_pers_email]  # Replace with actual employee email
            send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
            # Mail to HR
            subject = f'Final Approval - {exit_request.emp_code.emp_name}'
            messagemail = f"Dear HR, This notification confirms the final approval of {exit_request.emp_code.emp_name}'s resignation. All necessary IT, security, and finance clearances are complete; please proceed with the final offboarding steps."
            hr_user = extras.hr_spoc_id
            if hr_user:
                hr_email = EmployeeBasic.objects.get(user=hr_user).emp_pers_email
                recipient_list = [hr_email] # Replace with actual HR email
                send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
            return redirect('finance_approvals') # Redirect to the new security view
        elif status == 'Rejected':
            extras.finance_reviewed = True
            extras.finance_approved = False
            extras.rejected_by = "Finance"
            extras.save()
            exit_request.status = 'Rejected'
            message = 'Resignation rejected successfully'
            # Mail to employee
            subject = f'Update on your resignation - {exit_request.emp_code.emp_name}'
            messagemail = f"Dear {exit_request.emp_code.emp_name}, Your resignation request has been rejected by finance. Please contact HR for further assistance."
            recipient_list = [exit_request.emp_code.emp_pers_email]  # Replace with actual employee email
            send_mail(subject, messagemail, settings.DEFAULT_FROM_EMAIL, recipient_list)
        exit_request.save()
        extras.save()
        return render(request, 'update_exit_status_fin.html', {'exit_request': exit_request, 'action_success':True, 'message':message})
        #return render(request, 'update_exit_status_fin.html', {'exit_request': exit_request, 'action_success':True})
    return render(request, 'update_exit_status_fin.html', {'exit_request': exit_request})


@never_cache
@login_required
def disable_email(request: HttpRequest, request_id):
    print(">>>> disable_email view triggered")
    req = get_object_or_404(Resignation, resign_id=request_id)
    print("Disabling email/system for:", req.emp_code.emp_name)
    extras, _ = ResignationExtras.objects.get_or_create(resignation=req)
    extras.email_disabled = True
    extras.save()  # Save now
    req.save()
    # Re-fetch fresh data from DB
    req = Resignation.objects.get(resign_id=request_id)
    extras, _ = ResignationExtras.objects.get_or_create(resignation=req)
    if extras.IT_spoc_id != request.user:
        return HttpResponseForbidden("You are not authorized to review this resignation.")
    if extras.email_disabled and extras.system_access_disabled:
        extras.it_clearance = True
        extras.save()
        req.save()
        # Mail to employee
        subject = f'Update on Your Resignation - {req.emp_code.emp_name}'
        message = f"Dear {req.emp_code.emp_name}, IT has disabled your email and system access."
        recipient_list = [req.emp_code.emp_pers_email]  # Replace with actual employee email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    print(f"Email disabled for: {req.emp_code.emp_name}, Status: {extras.email_disabled}")
    return HttpResponse(status=204)

@never_cache
@login_required
def disable_system_access(request: HttpRequest, request_id):
   req = get_object_or_404(Resignation, resign_id=request_id)
   print("Disabling email/system for:", req.emp_code.emp_name)
   extras, _ = ResignationExtras.objects.get_or_create(resignation=req)
   extras.system_access_disabled = True
   extras.save()
   req.save()
    # Re-fetch fresh data from DB
   req = Resignation.objects.get(resign_id=request_id)
   extras, _ = ResignationExtras.objects.get_or_create(resignation=req)
   print("[EMAIL] Email Disabled:", extras.email_disabled)
   print("[EMAIL] System Access Disabled:", extras.system_access_disabled)
   if extras.IT_spoc_id != request.user:
        return HttpResponseForbidden("You are not authorized to review this resignation.")

   if extras.email_disabled and extras.system_access_disabled:
        extras.it_clearance = True
        extras.save()
        req.save()
        # Mail to employee
        subject = f'Update on Your Resignation - {req.emp_code.emp_name}'
        message = f"Dear {req.emp_code.emp_name}, IT has disabled your email and system access."
        recipient_list = [req.emp_code.emp_pers_email]  # Replace with actual employee email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
   return HttpResponse(status=204)


def custom_password_reset(request: HttpRequest):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Logic for sending a password reset email or showing a success message
            messages.success(request, 'Password reset instructions have been sent to your email.')
        except User.DoesNotExist:
            messages.error(request, 'No user found with that email.')
        return redirect('custom_password_reset')
    return render(request, 'forgot_password.html')



@never_cache
@login_required
def it_approvals_mail(request: HttpRequest):
    if not request.user.groups.filter(name='it').exists():
        return render(request, 'unauthorized.html')

    # Only show resignations assigned to this IT user, needing email/system actions
    exit_requests = Resignation.objects.filter(
        extras__IT_spoc_id=request.user,
        extras__finance_reviewed=True,
        extras__finance_approved=True
    ).filter(
        extras__email_disabled=False
    ) | Resignation.objects.filter(
        extras__IT_spoc_id=request.user,
        extras__finance_reviewed=True,
        extras__finance_approved=True
    ).filter(
        extras__system_access_disabled=False
    )

    paginated_requests = paginate_queryset(request, exit_requests, per_page=6)

    return render(request, 'it_approvals_mail.html', {
        'user': request.user,
        'user_groups': list(request.user.groups.values_list('name', flat=True)),
        'it_exit_requests': paginated_requests
    })



@never_cache
@login_required
def manager_approvals(request):
    #exit_qs = Resignation.objects.filter(extras__forwarded_to_manager=True, extras__manager_reviewed=False, extras__manager_spoc_id=request.user)
    exit_qs = Resignation.objects.filter(extras__manager_reviewed=False, extras__manager_spoc_id=request.user)
    paginator = Paginator(exit_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'manager_approvals.html', {
        'exit_requests': page_obj,
        'pending_count': exit_qs.count()
    })

@never_cache
@login_required
def finance_approvals(request):
    exit_qs = Resignation.objects.filter(extras__security_clearance=True, extras__finance_reviewed=False, extras__finance_spoc_id=request.user)
    paginator = Paginator(exit_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, 'finance_approvals.html', {
        'exit_requests': page_obj,
        'pending_count': exit_qs.count()
    })


'''@login_required
@login_required
def hr_approvals(request):
    employee_basic = cast(EmployeeBasic, request.user.employeebasic)
    emp_code = employee_basic.emp_code
    employee = get_object_or_404(EmployeeBasic, emp_code=emp_code)
    #resignations = Resignation.objects.filter(pend_from='HR').select_related('emp_code').order_by('-resign_id')
    resignations = Resignation.objects.filter(
        extras__hr_spoc_id__isnull=True
    ).exclude(emp_code__user=request.user) | Resignation.objects.filter(
        extras__hr_spoc_id=request.user
    ).select_related('extras').order_by('-resign_id')
    paginated_resignations = paginate_queryset(request, resignations, per_page=6)

    paginator = Paginator(resignations, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'hr_approvals.html', {'resignations': page_obj})'''

@never_cache
@login_required
def hr_approvals(request):
    if not request.user.groups.filter(name='hr').exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Show only requests assigned to this HR user and not yet finally approved
    pending_resignations = Resignation.objects.filter(
        extras__hr_spoc_id=request.user,
        extras__final_hr_approved=False
    ).select_related('extras').order_by('-resign_id')

    # Include unassigned ones as well
    unassigned_resignations = Resignation.objects.filter(
        extras__hr_spoc_id__isnull=True
    ).exclude(emp_code__user=request.user).select_related('extras')

    combined_qs = (pending_resignations | unassigned_resignations).distinct()
    paginated_resignations = paginate_queryset(request, combined_qs, per_page=6)

    return render(request, 'hr_approvals.html', {
        'resignations': paginated_resignations
    })


TOPIC_KEYWORDS = {
    'Speed': ['speed', 'delay', 'slow', 'timing'],
    'Notifications': ['email', 'notification', 'alert'],
    'Workflow': ['workflow', 'process', 'steps'],
    'Settlement': ['settlement', 'dues', 'salary'],
    'Usability': ['usability', 'ease', 'navigation'],
    'UI': ['UI', 'interface', 'design'],
    'Support': ['support', 'help', 'assistance'],
    'Experience': ['experience', 'journey', 'time'],
    'IT': ['IT', 'system', 'access', 'laptop'],
    'HR': ['HR', 'human resource'],
}

def extract_topics_with_gemini(text):
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = (
            "Extract 3-5 meaningful topics or issues from this employee exit feedback. "
            "Be concise, but highlight complaints, friction points, or appreciation. "
            "Even if feedback is short, infer probable concerns. "
            "Return only a comma-separated list of keywords, no extra text."
            "The topics should be professional and relevant to the context of the feedback.\n\n"
            f"Feedback:\n{text}"
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",  # or gemini-pro if preferred
            contents=prompt,
        )

        keywords = response.text.strip()

        # Clean & return as a list
        return [kw.strip() for kw in keywords.split(",") if kw.strip()]

    except Exception as e:
        print("Gemini keyword extraction error:", e)
        return ["Keyword extraction failed"]


def generate_summary_with_gemini(text):
    try:
        print("Calling Gemini with text:", text)
        client = genai.Client(api_key=settings.GEMINI_API_KEY)  # TEMPORARY TEST ONLY
        #model = genai.GenerativeModel('models/gemini-pro')

        response = client.models.generate_content( model="gemini-2.0-flash",  # You can also try "gemini-pro"
                                                  contents=f"Summarize the following feedback in 1 short sentence. The summary must be professional and relevant to the context of the feedback:\n\n{text}\n\n")
        print("Gemini response object:", response)
        
        if hasattr(response, 'text') and response.text:
            print("Gemini summary:", response.text.strip())
            return response.text.strip()
        else:
            return "Gemini returned no text"
    except Exception as e:
        print("Gemini API error:", e)
        return "Summary generation failed"
    

def classify_sentiment_with_gemini(text):
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = (
            "You are analyzing employee exit feedback. "
            "Classify the sentiment strictly as **Positive**, **Negative**, or **Mixed**. "
            "Be sensitive to frustration, dissatisfaction, or complaints even if they're subtle. "
            "Avoid assuming neutrality in short responses. Respond with only one of the three words.\n\n"
            f"Feedback:\n{text}"
        )


        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        label = response.text.strip().capitalize()

        if label in ["Positive", "Negative", "Mixed"]:
            return label
        else:
            return "Mixed"  # fallback
    except Exception as e:
        print("Gemini sentiment error:", e)
        return "Mixed"


def analyze_feedback_text(text):
    # Sentiment
    """blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        sentiment = "Positive"
    elif polarity < -0.1:
        sentiment = "Negative"
    else:
        sentiment = "Mixed"""
    
    sentiment = classify_sentiment_with_gemini(text)
    # Topics
    topics = extract_topics_with_gemini(text)

    # Summary
    summary = generate_summary_with_gemini(text)


    return sentiment, topics, summary


@never_cache
@login_required
def feedback_analysis(request):
    if not request.user.groups.filter(name='hr').exists():
        return HttpResponseForbidden()

    # Step 1: Get resignations assigned to this HR user
    assigned_resignations = ResignationExtras.objects.filter(hr_spoc_id=request.user).values_list('resignation_id', flat=True)

    # Step 2: Get feedbacks linked to those resignations, newest first
    feedbacks = Feedback.objects.filter(resign_id__in=assigned_resignations).select_related('resign_id', 'user').order_by('-id')

    # Step 3: Analyze feedback content
    analysis_data = []
    for fb in feedbacks:
        analysis_data.append({
            'id': fb.id,
            'resignation_id': fb.resign_id.resign_id,
            'employee_name': fb.user.get_full_name(),
            'sentiment': fb.sentiment or 'Not Available',
            'topics': fb.topics or 'Not Available',
            'summary': fb.summary or 'Not Available',
        })

    return render(request, 'feedback_analysis.html', {'feedback_analysis': analysis_data})


@never_cache
@login_required
def manager_approved_requests(request):
    if not request.user.groups.filter(name='manager').exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    approved_requests = Resignation.objects.filter(
        extras__manager_spoc_id=request.user,
        extras__manager_reviewed=True,
        extras__manager_approved=True
    ).select_related('emp_code', 'extras').order_by('-resign_id')

    paginated_requests = paginate_queryset(request, approved_requests, per_page=6)

    return render(request, 'manager_approved_requests.html', {
        'approved_requests': paginated_requests
    })


@never_cache
@login_required
def finance_approved_requests(request):
    if not request.user.groups.filter(name='finance').exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    approved_requests = Resignation.objects.filter(
        extras__finance_spoc_id=request.user,
        extras__finance_reviewed=True,
        extras__finance_approved=True
    ).select_related('emp_code', 'extras').order_by('-resign_id')

    paginated_requests = paginate_queryset(request, approved_requests, per_page=6)

    return render(request, 'finance_approved_requests.html', {
        'approved_requests': paginated_requests
    })

@never_cache
@login_required
def hr_approved_requests(request):
    if not request.user.groups.filter(name='hr').exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    approved_requests = Resignation.objects.filter(
        extras__hr_spoc_id=request.user,
        extras__final_hr_approved=True
    ).select_related('emp_code', 'extras').order_by('-resign_id')

    paginated_requests = paginate_queryset(request, approved_requests, per_page=6)

    return render(request, 'hr_approved_requests.html', {
        'approved_requests': paginated_requests
    })


# New view for Security

@never_cache
@login_required
def security_view(request: HttpRequest):
    if not request.user.groups.filter(name='security').exists():
        return render(request, 'unauthorized.html')

    exit_requests = Resignation.objects.filter(
        extras__manager_reviewed=True,
        extras__manager_approved=True,
        extras__security_clearance=False,
        extras__security_spoc_id=request.user
    ).select_related('emp_code', 'extras').prefetch_related('assets_for_exit__asset').distinct()

    return render(request, 'security_approvals.html', {
        'exit_requests': exit_requests,
    })



@never_cache
@login_required
def security_approve_asset(request, resign_id):
    if not request.user.groups.filter(name='security').exists():
        return HttpResponseForbidden("Not authorized.")

    resignation = get_object_or_404(Resignation, resign_id=resign_id)
    extras, _ = ResignationExtras.objects.get_or_create(resignation=resignation)

    if extras.security_spoc_id != request.user:
        return HttpResponseForbidden("You are not assigned to this request.")

    # Get related assets
    asset_extras = AssetExtras.objects.filter(assigned_for_exit=resignation).select_related('asset')

    if request.method == 'POST':
        # Save returned status from checkboxes
        for ae in asset_extras:
            checkbox_name = f'returned_{ae.id}'
            ae.returned = checkbox_name in request.POST
            ae.save()

        # Recheck all returned
        all_returned = all(ae.returned for ae in asset_extras)

        if not all_returned:
            return render(request, 'security_approve_asset.html', {
                'resignation': resignation,
                'assets': asset_extras,
                'error': "Cannot approve: not all assets have been returned."
            })

        # Mark security clearance
        extras.security_clearance = True
        extras.security_done = True
        extras.save()
        # Mail to employee
        subject = f'Update on Your Resignation - {resignation.emp_code.emp_name}'
        message = f"Dear {resignation.emp_code.emp_name}, Security has verified your asset return. Your request has been forwarded to the finance department for review. You will be notified once the finance has reviewed your request."
        recipient_list = [resignation.emp_code.emp_pers_email]  # Replace with actual employee email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        # Mail to finance
        subject = f'Employee Resignation - Action for Finance: {resignation.emp_code.emp_name}'
        message =  message=f"Dear finance, Please be advised that {resignation.emp_code.emp_name} has resigned. All IT and security offboarding procedures have been completed, so please process their final salary, outstanding dues, and provident fund settlements accordingly."
        finance_user = extras.finance_spoc_id
        if finance_user:
            finance_email = EmployeeBasic.objects.get(user=finance_user).emp_pers_email
        recipient_list = [finance_email]  # Replace with actual finance email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

        return redirect('security_view')

    # GET request
    all_returned = all(ae.returned for ae in asset_extras)

    return render(request, 'security_approve_asset.html', {
        'resignation': resignation,
        'assets': asset_extras,
        'all_returned': all_returned
    })

