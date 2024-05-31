# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cv-generator/', views.cv_generator, name='cv_generator'),
    path('cvs-created/', views.cvs_created, name='cvs_created'),
    path('cv/<int:pk>/', views.cv_view, name='cv_view'),
    path('cv-download/<int:cv_id>/', views.cv_download, name='cv_download'),
    path('cv-delete/<int:cv_id>/', views.cv_delete, name='cv_delete'),
    path('profile/', views.profile, name='profile'),
    path('login_user/', views.login_user, name='login_user'),
    path('register_user/', views.register_user, name='register_user'),
    path('logout_user/', views.logout_user, name='logout_user'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('verify/<str:myuuid>/', views.verify, name='verify'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    
]
