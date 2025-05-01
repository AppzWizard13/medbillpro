from django.urls import path
from .views import UserRegistrationView, LoginView, LogoutView, UserListView, UserDetailView, UserUpdateView, UserDeleteView

urlpatterns = [
    path('api/auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('api/auth/login/', LoginView.as_view(), name='user-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='user-logout'),

    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('api/users/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('api/users/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
]