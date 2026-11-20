from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/live-search/', views.live_search, name='live_search'),
    path('api/auth/register/', views.auth_register, name='auth_register'),
    path('api/auth/login/', views.auth_login, name='auth_login'),
    path('api/auth/logout/', views.auth_logout, name='auth_logout'),
    path('api/profile/save/', views.save_profile, name='save_profile'),
    path('api/add-review/', views.add_review, name='add_review'),
    path('api/contact/', views.send_contact, name='send_contact'),
    path('api/create-order/', views.create_order, name='create_order'),
    path('api/verify-payment/', views.verify_payment, name='verify_payment'),
    path('api/track-orders/', views.track_orders, name='track_orders'),
    path('api/orders/cancel/', views.cancel_order, name='cancel_order'),
    path('api/orders/exchange/', views.request_exchange, name='request_exchange'),
]