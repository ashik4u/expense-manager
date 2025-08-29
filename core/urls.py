from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import vendor_balance

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/add/', views.vendor_add, name='vendor_add'),
    path('vendors/<str:name>/summary/', views.vendor_summary, name='vendor_summary'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('returns/<int:pk>/', views.return_detail, name='return_detail'),
    path('adjustments/<int:pk>/', views.adjustment_detail, name='adjustment_detail'),
    path('adjustments/<int:pk>/edit/', views.adjustment_edit, name='adjustment_edit'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('returns/', views.return_list, name='return_list'),
    path('returns/add/', views.return_add, name='return_add'),
    path('returns/<int:pk>/edit/', views.return_edit, name='return_edit'),
    path('returns/<int:pk>/delete/', views.return_delete, name='return_delete'),
    path('ajax/products-by-vendor/', views.ajax_products_by_vendor, name='ajax_products_by_vendor'),
    path('adjustments/', views.adjustment_list, name='adjustment_list'),
    path('adjustments/add/', views.adjustment_add, name='adjustment_add'),
    path('select2/', include('django_select2.urls')),
    path('api/vendor-balance/', vendor_balance),
    path('accounts/', include('django.contrib.auth.urls')),  # Add this line
    path('sidebar-test/', views.sidebar_test, name='sidebar_test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
