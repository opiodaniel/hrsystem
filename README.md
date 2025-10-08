# hrsystem
A Django + Firebase system for managing employees and clients with secure login and role-based access.



# 🧭 Employee & Client Management System (Firebase + Django)

![Framework](https://img.shields.io/badge/Django%20Framework-green)
![Database](https://img.shields.io/badge/Firebase-cloud%20%26%20storage-blue)

📌 Overview

This is a role-based Employee & Client Management System built with Django on the backend and Firebase Authentication for secure user management.

✅ Employees can log in and manage only the clients they register.

👑 Admins have a dedicated dashboard to manage employees, view overall system data, and access advanced features.

🔐 Access to different pages is restricted based on user roles (Admin or Employee).

🚀 All employee registrations happen via AJAX for a smooth user experience.

🏗️ Tech Stack
Layer	Technology
Backend	Django (Python)
Authentication	Firebase Authentication
Frontend	HTML, CSS, JavaScript, AJAX, jQuery
Alerts / UI Feedback	SweetAlert2
Database (optional)	Firebase Realtime DB or Firestore (optional for client data)
Session Management	Django sessions
🧑‍💻 Features
🔐 Authentication

Secure login and registration through Firebase Authentication.

Session-based access control in Django.

Role-based permissions (Admin vs Employee).

🧭 Admin Dashboard

View total number of employees.

Register new employees via a modal form without page reload.

Live updates to dashboard using AJAX.

View a list of registered employees.

👷 Employee Dashboard

View and manage only the clients they registered.

Add, view, and edit client entries.

Simplified and restricted access compared to admins.

🛡️ Role-Based Access Control
Role	Access
Admin	Admin dashboard, register employees, view all employees and clients
Employee	Employee dashboard, view and manage only their clients
Guest	No access; redirected to login
---

## Getting Started (Local Development)

### Prerequisites
Ensure you have the following installed:
* Python (3.9+)
* Node.js & npm (18+)
* Git

### 1. Project Setup
```bash
# Clone the repository
git clone https://github.com/opiodaniel/feyti-medical-assistant.git
cd feyti-medical-assistant

2. Backend Setup (Django API)
Navigate to the backend directory and set up a virtual environment:
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Run Migrations (creates the SQLite database and tables):
python manage.py makemigrations reports
python manage.py migrate

Start the Django API Server:
python manage.py runserver 8000
# The API will be available at http://localhost:8000/api/

3. Frontend Setup (React UI)
Open a new terminal window, navigate to the frontend directory:
cd ../frontend
npm install

Start the React Development Server:
npm run dev
# The UI will open at http://localhost:<port_number> (e.g., 5173 or 3000)

