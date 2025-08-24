from django.contrib.admin import AdminSite
from django.db.models import Sum

# Custom admin site with vendor balance summary
class CustomAdminSite(AdminSite):
    site_header = 'Expense Manager Admin'
    site_title = 'Expense Manager Admin Portal'
    index_title = 'Dashboard'

    def each_context(self, request):
        context = super().each_context(request)
        total_balance = Vendor.objects.aggregate(total=Sum('opening_balance'))['total'] or 0
        context['total_vendor_balance'] = total_balance
        return context

custom_admin_site = CustomAdminSite(name='custom_admin')
from django.contrib.admin import AdminSite
from django.db.models import Sum

# Custom admin site with vendor balance summary
class CustomAdminSite(AdminSite):
    site_header = 'Expense Manager Admin'
    site_title = 'Expense Manager Admin Portal'
    index_title = 'Dashboard'

    def each_context(self, request):
        context = super().each_context(request)
        total_balance = Vendor.objects.aggregate(total=Sum('opening_balance'))['total'] or 0
        context['total_vendor_balance'] = total_balance
        return context

custom_admin_site = CustomAdminSite(name='custom_admin')
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django_select2.forms import ModelSelect2Widget
from .models import Vendor, Product, Expense, Payment, Return, Adjustment, ExpenseProduct


# Inline for ExpenseProduct
class ExpenseProductInline(admin.TabularInline):
    model = ExpenseProduct
    extra = 0
    fields = ['product', 'quantity']
    readonly_fields = ['subtotal_html']

    def subtotal_html(self, obj=None):
        # Render a cell for JS to update
        value = obj.product.price * obj.quantity if obj and obj.product and obj.quantity else '-'
        return format_html('<span class="expenseproduct-subtotal">{}</span>', value)
    subtotal_html.short_description = 'Subtotal'

    class Media:
        js = ('admin/js/expenseproduct_subtotal.js',)

class ExpenseAdminForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'vendor': forms.Select,
        }

class ExpenseAdmin(admin.ModelAdmin):

    form = ExpenseAdminForm
    inlines = [ExpenseProductInline]
    readonly_fields = ['amount']
    list_display = ['date', 'vendor_name', 'amount', 'view_memo_icon']

    def vendor_name(self, obj):
        if obj.vendor:
            url = f"/admin/core/vendor/{obj.vendor.id}/change/"
            return format_html("<a href='{}' target='_blank'>{}</a>", url, obj.vendor.name)
        return "-"
    vendor_name.short_description = 'Vendor Name'

    def view_memo_icon(self, obj):
        if hasattr(obj, 'memo') and obj.memo:
            icon_html = "<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='currentColor' viewBox='0 0 16 16'><path d='M4 0h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H4zm1 2h6v1H5V3zm0 2h6v1H5V5zm0 2h6v1H5V7z'/></svg>"
            return format_html("<a href='{}' target='_blank'>{}</a>", obj.memo.url, format_html(icon_html))
        return "-"
    view_memo_icon.short_description = 'View Memo'


    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        expense = form.instance
        expense.amount = expense.subtotal() + expense.delivery_charge
        expense.save(update_fields=["amount"])


class VendorAdmin(admin.ModelAdmin):
    readonly_fields = ['current_balance', 'latest_transactions']
    list_display = ['name', 'contact', 'current_balance']

    def current_balance(self, obj):
        expenses = sum([e.amount for e in obj.expenses.all()])
        payments = sum([p.amount for p in obj.payments.all()])
        returns = sum([r.amount for r in obj.returns.all()])
        adjustments = sum([a.amount for a in obj.adjustments.all()])
        # User requirement: expense should be added, payment/return deducted
        return obj.opening_balance + expenses - payments - returns + adjustments
    current_balance.short_description = 'Current Balance'


    def latest_transactions(self, obj):
        txns = []
        # Expenses: show each product in the expense
        for e in obj.expenses.order_by('-date')[:5]:
            for ep in e.expense_products.all():
                url = f"/admin/core/expense/{e.id}/change/"
                view_html = f"<a href='{url}' target='_blank' title='View Expense'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
                txns.append((e.date, 'Expense', ep.product.name, ep.quantity, ep.product.price * ep.quantity, view_html))
        # Payments
        for p in obj.payments.order_by('-date')[:5]:
            url = f"/admin/core/payment/{p.id}/change/"
            view_html = f"<a href='{url}' target='_blank' title='View Payment'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
            txns.append((p.date, f'Payment ({p.method})', '', '', p.amount, view_html))
        # Returns: show product and quantity
        for r in obj.returns.order_by('-date')[:5]:
            url = f"/admin/core/return/{r.id}/change/"
            view_html = f"<a href='{url}' target='_blank' title='View Return'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
            txns.append((r.date, 'Return', r.product.name, '', r.amount, view_html))
        # Adjustments
        for a in obj.adjustments.order_by('-date')[:5]:
            url = f"/admin/core/adjustment/{a.id}/change/"
            view_html = f"<a href='{url}' target='_blank' title='View Adjustment'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
            txns.append((a.date, 'Adjustment', '', '', a.amount, view_html))
        txns = sorted(txns, key=lambda x: x[0], reverse=True)[:5]
        if not txns:
            return "No recent transactions"
        html = ["<table style='border-collapse:collapse;'>",
                "<tr><th style='border:1px solid;padding:4px;'>Date</th><th style='border:1px solid;padding:4px;'>Type</th><th style='border:1px solid;padding:4px;'>Product</th><th style='border:1px solid;padding:4px;'>Quantity</th><th style='border:1px solid;padding:4px;'>Amount</th><th style='border:1px solid;padding:4px;'>View</th></tr>"]
        for date, txn_type, product, quantity, amount, view_html in txns:
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%d-%b-%Y')
            else:
                date_str = str(date)
            html.append(f"<tr><td style='border:1px solid;padding:4px;'>{date_str}</td><td style='border:1px solid;padding:4px;'>{txn_type}</td><td style='border:1px solid;padding:4px;'>{product}</td><td style='border:1px solid;padding:4px;'>{quantity}</td><td style='border:1px solid;padding:4px;'>{amount}</td><td style='border:1px solid;padding:4px;text-align:center'>{view_html}</td></tr>")
        html.append("</table>")
        return format_html(''.join(html))
    latest_transactions.short_description = 'Latest Transactions'


    def latest_transactions(self, obj):
        txns = []
        # Expenses: show each product in the expense
        for e in obj.expenses.order_by('-date')[:5]:
            for ep in e.expense_products.all():
                url = f"/admin/core/expense/{e.id}/change/"
                view_html = f"<a href='{url}' target='_blank' title='View Expense'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
                txns.append((e.date, 'Expense', ep.product.name, ep.quantity, ep.product.price * ep.quantity, view_html))
        # Payments
        for p in obj.payments.order_by('-date')[:5]:
            url = f"/admin/core/payment/{p.id}/change/"
            view_html = f"<a href='{url}' target='_blank' title='View Payment'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
            txns.append((p.date, f'Payment ({p.method})', '', '', p.amount, view_html))
        # Returns: show product and quantity
        for r in obj.returns.order_by('-date')[:5]:
            url = f"/admin/core/return/{r.id}/change/"
            view_html = f"<a href='{url}' target='_blank' title='View Return'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
            txns.append((r.date, 'Return', r.product.name, '', r.amount, view_html))
        # Adjustments
        for a in obj.adjustments.order_by('-date')[:5]:
            url = f"/admin/core/adjustment/{a.id}/change/"
            view_html = f"<a href='{url}' target='_blank' title='View Adjustment'><svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='currentColor' viewBox='0 0 16 16'><path d='M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zm-8 4.5c-3.314 0-6-3.134-6-4.5s2.686-4.5 6-4.5 6 3.134 6 4.5-2.686 4.5-6 4.5z'/><path d='M8 5.5A2.5 2.5 0 1 0 8 10a2.5 2.5 0 0 0 0-4.5zM8 9a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z'/></svg></a>"
            txns.append((a.date, 'Adjustment', '', '', a.amount, view_html))
        txns = sorted(txns, key=lambda x: x[0], reverse=True)[:5]
        if not txns:
            return "No recent transactions"
        html = ["<table style='border-collapse:collapse;'>",
                "<tr><th style='border:1px solid;padding:4px;'>Date</th><th style='border:1px solid;padding:4px;'>Type</th><th style='border:1px solid;padding:4px;'>Product</th><th style='border:1px solid;padding:4px;'>Quantity</th><th style='border:1px solid;padding:4px;'>Amount</th><th style='border:1px solid;padding:4px;'>View</th></tr>"]
        for date, txn_type, product, quantity, amount, view_html in txns:
            if hasattr(date, 'strftime'):
                date_str = date.strftime('%d-%b-%Y')
            else:
                date_str = str(date)
            html.append(f"<tr><td style='border:1px solid;padding:4px;'>{date_str}</td><td style='border:1px solid;padding:4px;'>{txn_type}</td><td style='border:1px solid;padding:4px;'>{product}</td><td style='border:1px solid;padding:4px;'>{quantity}</td><td style='border:1px solid;padding:4px;'>{amount}</td><td style='border:1px solid;padding:4px;text-align:center'>{view_html}</td></tr>")
        html.append("</table>")
        return format_html(''.join(html))
    latest_transactions.short_description = 'Latest Transactions'


# Register models in sorted order for admin sidebar
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Expense, ExpenseAdmin)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'amount', 'method', 'date', 'view_memo_icon']

    def view_memo_icon(self, obj):
        if hasattr(obj, 'memo') and obj.memo:
            icon_html = "<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='currentColor' viewBox='0 0 16 16'><path d='M4 0h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H4zm1 2h6v1H5V3zm0 2h6v1H5V5zm0 2h6v1H5V7z'/></svg>"
            return format_html("<a href='{}' target='_blank'>{}</a>", obj.memo.url, format_html(icon_html))
        return "-"
    view_memo_icon.short_description = 'View Memo'

admin.site.register(Payment, PaymentAdmin)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'vendor']

admin.site.register(Product, ProductAdmin)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'product', 'quantity', 'amount', 'date']

admin.site.register(Return, ReturnAdmin)
class AdjustmentAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'amount', 'date']

admin.site.register(Adjustment, AdjustmentAdmin)
