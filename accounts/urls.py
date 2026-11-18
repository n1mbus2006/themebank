from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('accounts/login/', views.LoginViewCustom.as_view(), name='login'),
    path('accounts/logout/', views.LogoutViewCustom.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/password_change/', views.PasswordChangeViewCustom.as_view(),
         name='password_change'),
    path('accounts/password_change/done/', views.PasswordChangeDoneViewCustom.as_view(),
         name='password_change_done'),
]
