from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from firebase_admin import auth
from hrmanager.settings import db
from firebase_admin import firestore
import firebase_admin
import requests
from django.conf import settings
from django.contrib.auth import logout
from .decorators import firebase_login_required, admin_required

def register_form(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")

        if password1 != password2:
            return JsonResponse({"status": "error", "message": "Passwords do not match."}, status=400)

        try:
            user = auth.create_user(
                email=email,
                password=password1,
                display_name=f"{first_name} {last_name}"
            )
            # Store additional info in Firestore
            db.collection('distributors').document(user.uid).set({
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
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
            "username": user_record.display_name or "",
            "email": user_record.email,
            "first_name": (user_record.display_name or "").split()[0] if user_record.display_name else "",
            "last_name": (user_record.display_name or "").split()[-1] if user_record.display_name else "",
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
            "username": user_record.display_name or "",
            "email": user_record.email,
            "first_name": (user_record.display_name or "").split()[0] if user_record.display_name else "",
            "last_name": (user_record.display_name or "").split()[-1] if user_record.display_name else "",
        })

    context = {
        "user": user,
        "employees": distributors,
        "total_employees": len(distributors),
    }
    return render(request, "distributor_list.html", context)