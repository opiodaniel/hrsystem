# hrsystem
A Django + Firebase system for managing employees and clients with secure login and role-based access.



# feyti-medical-assistant
AI Regulatory Report Assistant: Full-stack application built with Django REST Framework and React to structure adverse medical event reports using rule-based NLP logic.



# 🔬 AI Regulatory Report Assistant (Django/React Full-Stack)

![Backend](https://img.shields.io/badge/Backend-Django%20REST%20Framework-green)
![Frontend](https://img.shields.io/badge/Frontend-React%20%26%20Vercel-blue)
![NLP Logic](https://img.shields.io/badge/Logic-Rule--Based%2FPython-informational)

## Project Overview

This is a full-stack take-home assignment simulating a core workflow for Feyti Medical Group's AIcyclinder platform. The application processes raw adverse event text reports and extracts key structured data points using Python logic, presenting the results via a decoupled React frontend.

The project is split into two components:
1.  **Backend:** A REST API built with Django REST Framework (DRF) handling the report processing and data storage.
2.  **Frontend:** A modern web interface built with React (Vite) that consumes the API.

**Live Demo:**
* **Frontend (Vercel):** https://feyti-medical-group.vercel.app/
* **Backend API (Render):** https://feyti-medical-group-backend.onrender.com/

---

## Features Implemented

### Core Requirements
* **POST /api/process-report:** Accepts raw report text and returns structured JSON data.
* **NLP/Rule-Based Logic:** Extracts Drug Name, Adverse Events, Severity, and Outcome.
* **React Input Form:** A text area to paste reports and a "Process" button.
* **Results Display:** Clear presentation of the structured data on the frontend.

### Bonus Features
* **Simple Database (SQLite):** Reports are stored after processing.
* **GET /api/reports:** Endpoint to fetch a history of all processed reports.
* **Translation API:** **POST /api/translate** to translate the outcome to French/Swahili.
* **History View:** A table on the frontend showing past reports.

---

## Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python, Django, Django REST Framework | Handles API routing, database, and business logic. |
| **Database** | SQLite3 (Default Django DB) | Simple persistent storage for processed reports. |
| **Logic** | Custom Python Rule-Based Extractor | Uses string matching and regex for core extraction. |
| **Frontend** | React (Vite), Axios | Single Page Application (SPA) for the user interface and API communication. |
| **Deployment** | Vercel (Frontend), Render (Backend) | Hosted and accessible demo. |

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

