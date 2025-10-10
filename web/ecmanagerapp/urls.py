from django.urls import path
from . import views

urlpatterns = [

    path('', views.login_form, name='login_form'),
    path('register/', views.register_form, name='register_form'),
    path('logout/', views.logout_form, name='logout_form'),

    path('delete-employee/', views.delete_employee, name='delete_employee'),

    path("admins/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("employee/dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path("admins/dashboard/distributors", views.distributor_list, name="distributor_list"),
    path("api/submit_client_lead/", views.submit_client_lead, name="submit_client_lead"),
]
