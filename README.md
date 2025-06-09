# Employee Exit Management System

This is a Django-based system to manage employee resignations. It supports role-based dashboards for Employees, HR, Managers, IT, Finance, and Security. Features include resignation submission, feedback collection, approval workflow, and exit letter generation.

## Features
- Submit resignation and feedback
- Role-based login and dashboards
- HR, Manager, IT, Security, Finance approvals
- Exit status tracking and letter generation

## Tech Stack
- Backend: Django
- Frontend: HTML, CSS, JavaScript
- Database: MySQL (default)

## How to Run
1. Clone the repository
2. Create a virtual environment and activate it
3. Run `pip install -r requirements.txt`
4. Run migrations and start server with `python manage.py runserver`

## Project Structure
    myproject/
├── myapp/
│ ├── models.py
│ ├── views.py
│ ├── forms.py
│ └── templates/
├── static/
├── db.sqlite3
├── manage.py
└── README.md