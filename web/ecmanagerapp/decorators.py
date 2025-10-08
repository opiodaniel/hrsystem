from django.shortcuts import redirect

def firebase_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if "user" not in request.session:
            return redirect("login_form")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        user = request.session.get("user")
        if not user or user.get("role") != "admin":
            return redirect("employee_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper
