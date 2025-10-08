from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_form, name='register_form'),
    path('login/', views.login_form, name='login_form'),
    path('logout/', views.logout_form, name='logout_form'),
    path("admins/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("employee/dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path("employee/dashboard/distributors", views.distributor_list, name="distributor_list"),
]
