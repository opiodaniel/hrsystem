import firebase_admin
from django.http import JsonResponse
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

def register_form(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        full_name = request.POST.get("full_name")

        if password1 != password2:
            return JsonResponse({"status": "error", "message": "Passwords do not match."}, status=400)

        try:
            user = auth.create_user(
                email=email,
                password=password1,
                display_name=full_name
            )
            # Store additional info in Firestore
            db.collection('distributors').document(user.uid).set({
                'full_name': full_name,
                'email': email,
                'role': 'employee',
                'created_at': firestore.SERVER_TIMESTAMP
            })
            return JsonResponse({"status": "success", "message": "Employee registered successfully!"})
        except Exception as e:
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
            doc_ref = db.collection("distributors").document(uid).get()

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
        db = firestore.client()  # Get a fresh DB client instance
        distributor_ref = db.collection('distributors').document(employee_uid)

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

    user = request.session.get("user")

    # Example: fetch all Firebase users (can be cached later)
    distributors = []
    for user_record in auth.list_users().iterate_all():
        distributors.append({
            "uid": user_record.uid,
            "email": user_record.email,
            "full_name": user_record.display_name
        })

    context = {
        "user": user,
        "employees": distributors,
        "total_employees": len(distributors),
    }
    return render(request, "distributor_list.html", context)