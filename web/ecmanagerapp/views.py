import json

import firebase_admin
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from firebase_admin import auth
from hrmanager.settings import db
from firebase_admin import firestore
import requests
from django.conf import settings
from django.contrib.auth import logout
from .decorators import firebase_login_required, admin_required
import datetime
from datetime import timezone
import pytz # Required for converting to local timezone

def register_form(request):
    if request.method == "POST":
        # Assume data comes from request.POST for form submission (not JSON)
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        full_name = request.POST.get("full_name")

        if password1 != password2:
            return JsonResponse({"status": "error", "message": "Passwords do not match."}, status=400)

        try:
            # Assume 'auth' is the initialized Firebase Auth client
            user = auth.create_user(
                email=email,
                password=password1,
                display_name=full_name
            )
            # Store additional info in Firestore using the correct Public Data Path
            # Public data (for sharing with other users or collaborative apps):
            # Collection path: MUST store in /artifacts/{appId}/public/data/distributors
            distributors_ref = db.collection(f'artifacts/{settings.FIREBASE_WEB_APP_ID}/public/data/distributors')

            distributors_ref.document(user.uid).set({
                'full_name': full_name,
                'email': email,
                'role': 'employee',
                'created_at': firestore.SERVER_TIMESTAMP
            })
            return JsonResponse({"status": "success", "message": "Employee registered successfully!"})
        except Exception as e:
            # Catch specific Firebase Auth exceptions here in a real app
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)



def login_form(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        try:
            # Firebase REST API for sign-in
            firebase_auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_WEB_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            response = requests.post(firebase_auth_url, json=payload)
            data = response.json()

            decoded_token = auth.verify_id_token(data['idToken'])
            uid = decoded_token["uid"]

            # Fetch role from Firestore
            doc_ref = db.collection(f'artifacts/{settings.FIREBASE_WEB_APP_ID}/public/data/distributors').document(uid).get()

            if doc_ref.exists:
                user_data = doc_ref.to_dict()
                request.session["user"] = {
                    "uid": uid,
                    "email": user_data["email"],
                    "role": user_data.get("role", "employee")
                }
                # Redirect based on role
                if user_data.get("role") == "admin":
                    return redirect("admin_dashboard")
                else:
                    return redirect("employee_dashboard")
            else:
                messages.error(request, "User data not found in Firestore.")
                return redirect("login_form")

        except Exception as e:
            messages.error(request, f"Login failed: {e}")
            return redirect("login_form")
    else:
        return render(request, "login_form.html")


def logout_form(request):
    logout(request)
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('login_form')



@require_POST
def delete_employee(request):
    """
    Handles the deletion of a user from both Firebase Auth and Firestore DB.
    Requires the user's UID to identify the records.
    """

    # 1. Retrieve the UID from the POST request (e.g., via an AJAX call)
    try:
        employee_uid = request.POST.get('uid')
        if not employee_uid:
            return JsonResponse({'success': False, 'message': 'User ID (UID) is required for deletion.'}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid request data.'}, status=400)

    try:
        # --- Step 1: Delete from Firebase Authentication ---
        # This revokes their access and removes their authentication record.
        auth.delete_user(employee_uid)

        # --- Step 2: Delete associated document from Firestore ---
        # The document is stored in the 'distributors' collection, keyed by the UID.
        distributor_ref = db.collection(f'artifacts/{settings.FIREBASE_WEB_APP_ID}/public/data/distributors').document(
            employee_uid)

        # Check if the document exists before attempting deletion (optional but robust)
        if distributor_ref.get().exists:
            distributor_ref.delete()

        # You may want to delete other related data here as well,
        # e.g., db.collection('employee_tasks').document(employee_uid).delete()

        return JsonResponse({
            'success': True,
            'message': f'Employee (UID: {employee_uid}) successfully deleted from Auth and Firestore.'
        })

    except firebase_admin.exceptions.FirebaseError as e:
        # Handle cases where the user might not exist in Auth
        error_message = f"Firebase error during deletion: {e}"
        print(error_message)
        return JsonResponse(
            {'success': False, 'message': 'Deletion failed due to a Firebase issue (User may not exist).'}, status=500)

    except Exception as e:
        # Handle general errors (e.g., Firestore connection issues)
        error_message = f"Unexpected error during employee deletion: {e}"
        print(error_message)
        return JsonResponse({'success': False, 'message': 'An unexpected error occurred during the deletion process.'},
                            status=500)


@firebase_login_required
def employee_dashboard(request):
    user = request.session.get("user")
    return render(request, "employee_dashboard.html", {"user": user})


@firebase_login_required
@admin_required
def admin_dashboard(request):
    user = request.session.get("user")

    # Example: fetch all Firebase users (can be cached later)
    employees = []
    for user_record in auth.list_users().iterate_all():
        employees.append({
            "uid": user_record.uid,
            "email": user_record.email,
            "full_name":user_record.display_name
        })

    context = {
        "user": user,
        "employees": employees,
        "total_employees": len(employees),
    }
    return render(request, "admin_dashboard.html", context)


@firebase_login_required
@admin_required
def distributor_list(request):
    """
    Renders the distributor list page, fetching user data and their
    last login time directly from Firebase Authentication.
    """
    user = request.session.get("user")

    distributors = []

    # Define the local timezone object based on Django settings (e.g., Africa/Kampala)
    local_tz = pytz.timezone(settings.TIME_ZONE)

    # Iterate through all user records from Firebase Auth
    for user_record in auth.list_users().iterate_all():

        # 1. Initialize last_login_time to "Never"
        last_login_time = "Never"

        # FIX: Access the last sign-in timestamp from user_metadata for ExportedUserRecord
        last_sign_in_ms = user_record.user_metadata.last_sign_in_timestamp

        # 2. Check if the user has ever signed in (timestamp is not None)
        if last_sign_in_ms:
            # Firebase timestamps are in milliseconds; convert to seconds
            last_sign_in_seconds = last_sign_in_ms / 1000.0

            # Convert UTC timestamp to a timezone-aware datetime object (UTC is standard)
            utc_dt = datetime.datetime.fromtimestamp(last_sign_in_seconds, tz=timezone.utc)

            # Convert the UTC datetime to the local timezone (e.g., Africa/Kampala)
            local_dt = utc_dt.astimezone(local_tz)

            # 3. Format the Python datetime object into the desired clean string,
            # using %Z to show the local timezone abbreviation (e.g., EAT)
            last_login_time = local_dt.strftime('%b %d, %Y %I:%M %p %Z')

        distributors.append({
            "uid": user_record.uid,
            "email": user_record.email,
            "full_name": user_record.display_name or user_record.email,  # Use email if display_name is not set
            "last_login": last_login_time,  # Now includes the local last login time
        })

    context = {
        "user": user,
        "employees": distributors,
        "total_employees": len(distributors),
    }
    return render(request, "distributor_list.html", context)


def check_for_duplicate_contact(contact):
    """
    CONCEPTUAL: Checks if a contact (email or phone) already exists in any client lead.

    This simulates the complex, multi-field, server-side check required
    to ensure uniqueness across the entire public 'clients' collection.

    Note: Firestore requires separate queries for each field check.
    """
    clients_ref = db.collection(f'artifacts/{settings.FIREBASE_WEB_APP_ID}/public/data/clients')

    # Check if contact is already in 'contact1' field
    # We query the normalized field in the database
    query1 = clients_ref.where('contact1', '==', contact).limit(1).get()
    if len(query1) > 0:
        return True

    # Check if contact is already in 'contact2' field
    query2 = clients_ref.where('contact2', '==', contact).limit(1).get()
    if len(query2) > 0:
        return True

    return False


# --- Client Submission Logic (Updated) ---
def submit_client_lead(request):
    """
    Django view to receive and save a new client lead to Firestore.
    Ensures the client is correctly associated with the authenticated employee.
    """
    # 1. Server-side Request and Authentication Check
    if request.method != 'POST':
        return HttpResponseBadRequest(json.dumps({'error': 'Only POST method allowed'}), status=405)

    # Assuming user authentication has been handled and 'request.user' is available
    user = request.session.get("user")

    if not user or 'uid' not in user:
        # The user must be logged in to submit a lead
        return JsonResponse({"error": "Authentication required. Employee not found in session."}, status=401)

    employee_uid = user['uid']

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON format'}), status=400)

    # Extract and clean data
    full_name = data.get('fullName', '').strip()
    initial_notes = data.get('initialNotes', '').strip()

    # --- FIX: Safely normalize contact_1 (Required) ---
    contact_1_raw = data.get('contact1')
    contact_1 = str(contact_1_raw).strip().lower() if contact_1_raw else None

    # --- FIX: Safely normalize contact_2 (Optional) ---
    contact_2_raw = data.get('contact2')
    contact_2 = str(contact_2_raw).strip().lower() if contact_2_raw else None

    # 2. Basic Server-side Data Validation
    if not full_name or len(full_name) < 3:
        return HttpResponseBadRequest(json.dumps({'error': 'Full name required.'}), status=400)

    if not contact_1 or len(contact_1) < 5:
        return HttpResponseBadRequest(json.dumps({'error': 'Primary contact required and must be valid.'}), status=400)

    if contact_2 and contact_1 == contact_2:
        return HttpResponseBadRequest(json.dumps({'error': 'Contacts cannot be identical.'}), status=400)

    # If the optional contact_2 was just an empty string and became None, we treat it as valid.
    if contact_2 == "":
        contact_2 = None

    # 3. CRITICAL: Contact Uniqueness Check
    # Check contact 1
    if check_for_duplicate_contact(contact_1):
        return HttpResponseBadRequest(
            json.dumps({'error': 'Primary contact already registered with another client.'}), status=409)

    # Check contact 2 (only if provided)
    if contact_2 and check_for_duplicate_contact(contact_2):
        return HttpResponseBadRequest(
            json.dumps({'error': 'Secondary contact already registered with another client.'}), status=409)

    # 4. Save to Database (FIRESTORE)
    try:
        # Path: /artifacts/{APP_ID}/public/data/clients
        clients_ref = db.collection(f'artifacts/{settings.FIREBASE_WEB_APP_ID}/public/data/clients')

        client_data = {
            'ownerId': employee_uid,  # Enforces client-to-employee ownership
            'fullName': full_name,
            'contact1': contact_1,  # Normalized contact
            'contact2': contact_2,  # Normalized contact (None if not provided)
            'initialNotes': initial_notes,
            'dateLogged': firestore.SERVER_TIMESTAMP  # Uses server time for reliable logging
        }

        # Save the new document
        update_time, doc_ref = clients_ref.add(client_data)

        # Returns success response with the new document ID
        return JsonResponse({'message': 'Client lead saved successfully', 'id': doc_ref.id}, status=201)

    except Exception as e:
        # Log error details here
        print(f"Firestore Save Error: {e}")
        return JsonResponse({'error': 'Database save failed.'}, status=500)

