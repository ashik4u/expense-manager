from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payment_add(request):
	from .models import Payment, Vendor
	if request.method != 'POST':
		return redirect('payment_list')
	vendor_id = request.POST.get('vendor')
	date = request.POST.get('date')
	amount = request.POST.get('amount')
	method = request.POST.get('method')
	memo = request.FILES.get('memo')
	errors = []
	debug_post = {
		'vendor': vendor_id,
		'date': date,
		'amount': amount,
		'method': method,
		'csrfmiddlewaretoken': request.POST.get('csrfmiddlewaretoken'),
	}
	if not vendor_id:
		errors.append('Vendor is required.')
	if not date:
		errors.append('Date is required.')
	if not amount:
		errors.append('Amount is required.')
	if not method:
		errors.append('Method is required.')
	vendors = Vendor.objects.all()
	payments = Payment.objects.select_related('vendor').all().order_by('-date')
	vendor_obj = None
	if vendor_id:
		try:
			vendor_obj = Vendor.objects.get(pk=vendor_id)
		except Vendor.DoesNotExist:
			vendor_obj = None
	if errors:
		context = {
			'payments': payments,
			'vendors': vendors,
			'add_errors': errors,
			'vendor': vendor_obj,
		}
		if request.headers.get('x-requested-with') == 'XMLHttpRequest':
			from django.template.loader import render_to_string
			modal_html = render_to_string('core/payment_add_modal_body.html', context, request=request)
			return JsonResponse({'success': False, 'modal_body': modal_html, 'debug_post': debug_post})
		else:
			return render(request, 'core/payment_list.html', context)
	try:
		vendor = get_object_or_404(Vendor, pk=vendor_id)
		Payment.objects.create(vendor=vendor, date=date, amount=amount, method=method, memo=memo if memo else None)
		if request.headers.get('x-requested-with') == 'XMLHttpRequest':
			return JsonResponse({'success': True})
		else:
			return redirect('vendor_summary', name=vendor.name)
	except Exception as e:
		context = {
			'payments': payments,
			'vendors': vendors,
			'add_errors': [str(e)],
			'vendor': vendor_obj,
		}
		if request.headers.get('x-requested-with') == 'XMLHttpRequest':
			from django.template.loader import render_to_string
			modal_html = render_to_string('core/payment_add_modal_body.html', context, request=request)
			return JsonResponse({'success': False, 'modal_body': modal_html, 'debug_post': debug_post})
		else:
			return render(request, 'core/payment_list.html', context)

@login_required
@require_POST
def payment_edit(request, pk):
	from .models import Payment, Vendor
	payment = get_object_or_404(Payment, pk=pk)
	vendor_id = request.POST.get('vendor')
	date = request.POST.get('date')
	amount = request.POST.get('amount')
	method = request.POST.get('method')
	memo = request.FILES.get('memo')
	errors = []
	if not vendor_id:
		errors.append('Vendor is required.')
	if not date:
		errors.append('Date is required.')
	if not amount:
		errors.append('Amount is required.')
	if not method:
		errors.append('Method is required.')
	if errors:
		vendors = Vendor.objects.all()
		payments = Payment.objects.select_related('vendor').all().order_by('-date')
		return render(request, 'core/payment_list.html', {
			'payments': payments,
			'vendors': vendors,
			'edit_errors': errors,
			'edit_payment': payment,
		})
	vendor = get_object_or_404(Vendor, pk=vendor_id)
	payment.vendor = vendor
	payment.date = date
	payment.amount = amount
	payment.method = method
	if memo:
		payment.memo = memo
	payment.save()
	# Redirect to vendor summary after edit
	return redirect('vendor_summary', name=payment.vendor.name)

@login_required
@require_POST
def payment_delete(request, pk):
	from .models import Payment
	payment = get_object_or_404(Payment, pk=pk)
	vendor_name = payment.vendor.name
	payment.delete()
	# Redirect to vendor summary after delete
	return redirect('vendor_summary', name=vendor_name)
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404

@login_required
@require_POST
def product_add(request):
	from .models import Product, Vendor
	name = request.POST.get('name')
	vendor_id = request.POST.get('vendor')
	price = request.POST.get('price')
	if name and vendor_id and price:
		vendor = get_object_or_404(Vendor, pk=vendor_id)
		Product.objects.create(name=name, vendor=vendor, price=price)
	return redirect('product_list')

@login_required
@require_POST
def product_edit(request, pk):
	from .models import Product, Vendor
	product = get_object_or_404(Product, pk=pk)
	name = request.POST.get('name')
	vendor_id = request.POST.get('vendor')
	price = request.POST.get('price')
	if name and vendor_id and price:
		vendor = get_object_or_404(Vendor, pk=vendor_id)
		product.name = name
		product.vendor = vendor
		product.price = price
		product.save()
		if request.headers.get('x-requested-with') == 'XMLHttpRequest':
			return JsonResponse({'success': True})
		# Redirect to vendor summary after edit
		return redirect('vendor_summary', name=product.vendor.name)
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return JsonResponse({'success': False, 'error': 'Missing fields'})
	return redirect('product_list')

@login_required
@require_POST
def product_delete(request, pk):
    from .models import Product
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('product_list')
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404

@login_required
@require_POST
def expense_delete(request, pk):
	from .models import Expense
	expense = get_object_or_404(Expense, pk=pk)
	vendor_name = expense.vendor.name
	expense.delete()
	return redirect('vendor_summary', name=vendor_name)
from django.shortcuts import redirect
@login_required
def expense_edit(request, pk):
	from .models import Expense, ExpenseProduct, Product, Vendor
	expense = get_object_or_404(Expense, pk=pk)
	products = Product.objects.all()
	vendors = Vendor.objects.all()
	errors = []
	if request.method == 'POST':
		vendor_id = request.POST.get('vendor')
		date = request.POST.get('date')
		from decimal import Decimal
		amount = request.POST.get('amount')
		delivery_charge = request.POST.get('delivery_charge')
		try:
			expense.amount = Decimal(amount)
		except Exception:
			expense.amount = 0
		try:
			expense.delivery_charge = Decimal(delivery_charge)
		except Exception:
			expense.delivery_charge = 0
		memo = request.FILES.get('memo')
		try:
			expense.vendor = Vendor.objects.get(pk=vendor_id)
		except Vendor.DoesNotExist:
			errors.append('Invalid vendor.')
		expense.date = date
	# Already set above as Decimal
		if memo:
			expense.memo = memo
		# Update ExpenseProduct entries
		# Remove old products
		ExpenseProduct.objects.filter(expense=expense).delete()
		# Add new products from form
		product_keys = [k for k in request.POST.keys() if k.startswith('product_')]
		for key in product_keys:
			idx = key.split('_')[1]
			product_id = request.POST.get(f'product_{idx}')
			quantity = request.POST.get(f'quantity_{idx}')
			if product_id and quantity:
				try:
					product = Product.objects.get(pk=product_id)
					qty = int(quantity)
					if qty > 0:
						ExpenseProduct.objects.create(expense=expense, product=product, quantity=qty)
				except Exception:
					continue
	expense.save()
	return redirect('vendor_summary', name=expense.vendor.name)
	return render(request, 'core/expense_edit.html', {
		'expense': expense,
		'products': products,
		'vendors': vendors,
		'errors': errors,
	})
from django.shortcuts import get_object_or_404
@login_required
def expense_detail(request, pk):
	from .models import Expense, Vendor, Product
	expense = get_object_or_404(Expense, pk=pk)
	vendors = Vendor.objects.all()
	products = Product.objects.all()
	expense_products = []
	for ep in expense.expense_products.all():
		subtotal = float(ep.quantity) * float(ep.product.price)
		expense_products.append({
			'name': ep.product.name,
			'quantity': ep.quantity,
			'price': ep.product.price,
			'subtotal': subtotal
		})
	context = {
		'expense': expense,
		'vendors': vendors,
		'products': products,
		'expense_products': expense_products
	}
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return render(request, 'core/expense_detail_modal.html', context)
	else:
		return render(request, 'core/expense_detail.html', context)

# Payment Detail View
@login_required
def payment_detail(request, pk):
	from .models import Payment, Vendor
	payment = get_object_or_404(Payment, pk=pk)
	vendors = Vendor.objects.all()
	return render(request, 'core/payment_detail.html', {
		'payment': payment,
		'vendors': vendors,
	})

# Return Detail View
@login_required
def return_detail(request, pk):
	from .models import Return, Vendor, Product
	ret = get_object_or_404(Return, pk=pk)
	vendors = Vendor.objects.all()
	products = Product.objects.all()
	return render(request, 'core/return_detail.html', {
		'return': ret,
		'vendors': vendors,
		'products': products,
	})

# Adjustment Detail View
@login_required
def adjustment_detail(request, pk):
	from .models import Adjustment, Vendor
	adj = get_object_or_404(Adjustment, pk=pk)
	vendors = Vendor.objects.all()
	return render(request, 'core/adjustment_detail.html', {
		'adjustment': adj,
		'vendors': vendors,
	})

# Adjustment Edit View (for modal)
from django.views.decorators.http import require_POST
@login_required
def adjustment_edit(request, pk):
	from .models import Adjustment, Vendor
	adj = get_object_or_404(Adjustment, pk=pk)
	if request.method == 'POST':
		if 'delete' in request.POST:
			vendor_name = adj.vendor.name
			adj.delete()
			return redirect('vendor_summary', name=vendor_name)
		vendor_id = request.POST.get('vendor')
		date = request.POST.get('date')
		amount = request.POST.get('amount')
		note = request.POST.get('note')
		errors = []
		if not vendor_id:
			errors.append('Vendor is required.')
		if not date:
			errors.append('Date is required.')
		if not amount:
			errors.append('Amount is required.')
		if errors:
			vendors = Vendor.objects.all()
			return render(request, 'core/vendor_summary.html', {
				'edit_errors': errors,
				'edit_adjustment': adj,
				'vendors': vendors,
			})
		vendor = get_object_or_404(Vendor, pk=vendor_id)
		adj.vendor = vendor
		adj.date = date
		adj.amount = amount
		adj.note = note
		adj.save()
		return redirect('vendor_summary', name=adj.vendor.name)
	vendors = Vendor.objects.all()
	return render(request, 'core/adjustment_detail.html', {
		'adjustment': adj,
		'vendors': vendors,
	})
@login_required
def vendor_summary(request, name):
	import urllib.parse
	from .models import Vendor, Expense, Payment, Return, Adjustment, Product
	vendor_name = urllib.parse.unquote(name)
	vendor = Vendor.objects.filter(name__iexact=vendor_name).first()
	if not vendor:
		from django.http import Http404
		raise Http404('Vendor not found')
	expenses = Expense.objects.filter(vendor=vendor).order_by('-date')
	payments = Payment.objects.filter(vendor=vendor).order_by('-date')
	returns = Return.objects.filter(vendor=vendor).order_by('-date')
	adjustments = Adjustment.objects.filter(vendor=vendor).order_by('-date')
	products = Product.objects.filter(vendor=vendor)  # Only this vendor's products

	# Handle payment creation from modal
	if request.method == 'POST' and 'amount' in request.POST and 'method' in request.POST:
		from .models import Payment
		date = request.POST.get('date')
		amount = request.POST.get('amount')
		method = request.POST.get('method')
		memo = request.FILES.get('memo')
		errors = []
		if not date:
			errors.append('Date is required.')
		if not amount:
			errors.append('Amount is required.')
		if not method:
			errors.append('Method is required.')
		if not errors:
			Payment.objects.create(vendor=vendor, date=date, amount=amount, method=method, memo=memo if memo else None)
			return redirect('vendor_summary', name=vendor.name)
		else:
			context = {
				'vendor': vendor,
				'expenses': expenses,
				'payments': payments,
				'returns': returns,
				'adjustments': adjustments,
				'products': products,
				'add_errors': errors,
			}
			return render(request, 'core/vendor_summary.html', context)

	# Handle adjustment creation from modal
	if request.method == 'POST' and 'amount' in request.POST and 'note' in request.POST and 'adjustment' in request.POST:
		from .models import Adjustment
		date = request.POST.get('date')
		amount = request.POST.get('amount')
		note = request.POST.get('note')
		errors = []
		if not date:
			errors.append('Date is required.')
		if not amount:
			errors.append('Amount is required.')
		if not errors:
			Adjustment.objects.create(vendor=vendor, date=date, amount=amount, note=note)
			return redirect('vendor_summary', name=vendor.name)
		else:
			context = {
				'vendor': vendor,
				'expenses': expenses,
				'payments': payments,
				'returns': returns,
				'adjustments': adjustments,
				'products': products,
				'add_errors': errors,
			}
			return render(request, 'core/vendor_summary.html', context)

	# Find latest transaction
	latest = None
	latest_type = None
	latest_date = None
	latest_amount = None
	latest_obj = None
	all_tx = []
	for obj in [*expenses, *payments, *returns, *adjustments]:
		all_tx.append((obj.date, obj))
	if all_tx:
		# Sort by date only, not by tuple (date, obj)
		all_tx.sort(key=lambda x: x[0], reverse=True)
		latest_date, latest_obj = all_tx[0]
		if isinstance(latest_obj, Expense):
			latest_type = 'Expense'
			latest_amount = latest_obj.amount
		elif isinstance(latest_obj, Payment):
			latest_type = 'Payment'
			latest_amount = latest_obj.amount
		elif isinstance(latest_obj, Return):
			latest_type = 'Return'
			latest_amount = latest_obj.amount
		elif isinstance(latest_obj, Adjustment):
			latest_type = 'Adjustment'
			latest_amount = latest_obj.amount
		latest = latest_obj

	context = {
		'vendor': vendor,
		'expenses': expenses,
		'payments': payments,
		'returns': returns,
		'adjustments': adjustments,
		'latest_type': latest_type,
		'latest_date': latest_date,
		'latest_amount': latest_amount,
		'latest': latest,
		'products': products,
	}
	return render(request, 'core/vendor_summary.html', context)
@login_required
def vendor_add(request):
	from .models import Vendor
	context = {}
	if request.method == 'POST':
		name = request.POST.get('name', '').strip()
		contact = request.POST.get('contact', '').strip()
		opening_balance = request.POST.get('opening_balance', '0').strip()
		errors = []
		success = None
		# Validation
		if not name:
			errors.append('Vendor name is required.')
		try:
			opening_balance_val = float(opening_balance)
		except ValueError:
			errors.append('Opening balance must be a number.')
			opening_balance_val = 0
		if not errors:
			Vendor.objects.create(name=name, contact=contact, opening_balance=opening_balance_val)
			success = 'Vendor added successfully!'
			context['success'] = success
			context['name'] = ''
			context['contact'] = ''
			context['opening_balance'] = '0'
		else:
			context['errors'] = errors
			context['name'] = name
			context['contact'] = contact
			context['opening_balance'] = opening_balance
	return render(request, 'core/vendor_add.html', context)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from .models import Vendor

@login_required
@api_view(['GET'])
def vendor_balance(request):
	total = Vendor.objects.aggregate(total=Sum('opening_balance'))['total'] or 0
	return Response({'total': total})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
@login_required
def dashboard(request):
	from .models import Vendor, Product, Expense, Payment, Return, Adjustment
	from django.db import models
	vendors = Vendor.objects.all()
	vendor_balances = []
	for vendor in vendors:
		expenses = vendor.expenses.aggregate(total=models.Sum('amount'))['total'] or 0
		payments = vendor.payments.aggregate(total=models.Sum('amount'))['total'] or 0
		returns = vendor.returns.aggregate(total=models.Sum('amount'))['total'] or 0
		adjustments = vendor.adjustments.aggregate(total=models.Sum('amount'))['total'] or 0
		balance = vendor.opening_balance + expenses - payments - returns + adjustments
		vendor_balances.append({
			'name': vendor.name,
			'contact': vendor.contact,
			'opening_balance': vendor.opening_balance,
			'expenses': expenses,
			'payments': payments,
			'returns': returns,
			'adjustments': adjustments,
			'balance': balance,
		})
	context = {
		'vendor_count': Vendor.objects.count(),
		'product_count': Product.objects.count(),
		'expense_count': Expense.objects.count(),
		'payment_count': Payment.objects.count(),
		'return_count': Return.objects.count(),
		'adjustment_count': Adjustment.objects.count(),
		'vendors': vendor_balances,
		'active_menu': 'dashboard',
	}
	return render(request, 'core/dashboard.html', context)

@login_required
def vendor_list(request):
		from .models import Vendor
		from django.db import models
		vendors = Vendor.objects.all()
		vendor_balances = []
		for vendor in vendors:
			expenses = vendor.expenses.aggregate(total=models.Sum('amount'))['total'] or 0
			payments = vendor.payments.aggregate(total=models.Sum('amount'))['total'] or 0
			returns = vendor.returns.aggregate(total=models.Sum('amount'))['total'] or 0
			adjustments = vendor.adjustments.aggregate(total=models.Sum('amount'))['total'] or 0
			balance = vendor.opening_balance + expenses - payments - returns + adjustments
			vendor_balances.append({
				'name': vendor.name,
				'contact': vendor.contact,
				'opening_balance': vendor.opening_balance,
				'expenses': expenses,
				'payments': payments,
				'returns': returns,
				'adjustments': adjustments,
				'balance': balance,
			})
		context = {
			'vendors': vendor_balances,
			'active_menu': 'vendors',
		}
		return render(request, 'core/vendor_list.html', context)

@login_required
def product_list(request):
	from .models import Product, Vendor
	products = Product.objects.select_related('vendor').all().order_by('-id')
	vendors = Vendor.objects.all()
	return render(request, 'core/product_list.html', {
		'products': products,
		'vendors': vendors,
		'active_menu': 'products',
	})

@login_required
def expense_list(request):
	from .models import Expense, Vendor, Product
	expenses = Expense.objects.select_related('vendor').all().order_by('-date')
	vendors = Vendor.objects.all()
	products = Product.objects.all()
	return render(request, 'core/expense_list.html', {
		'expenses': expenses,
		'vendors': vendors,
		'products': products,
		'active_menu': 'expenses',
	})

@login_required
def expense_add(request):
	from .models import Expense, ExpenseProduct, Product, Vendor
	errors = []
	vendors = Vendor.objects.all()
	products = Product.objects.all()
	if request.method == 'POST':
		vendor_id = request.POST.get('vendor')
		date = request.POST.get('date')
		from decimal import Decimal
		amount = request.POST.get('amount')
		delivery_charge = request.POST.get('delivery_charge')
		memo = request.FILES.get('memo')
		try:
			vendor = Vendor.objects.get(pk=vendor_id)
		except Vendor.DoesNotExist:
			errors.append('Invalid vendor.')
			vendor = None
		try:
			amount_val = Decimal(amount) if amount else Decimal('0')
		except Exception:
			amount_val = Decimal('0')
		try:
			delivery_charge_val = Decimal(delivery_charge) if delivery_charge else Decimal('0')
		except Exception:
			delivery_charge_val = Decimal('0')
		if vendor and date:
			expense = Expense.objects.create(
				vendor=vendor,
				date=date,
				amount=amount_val,
				delivery_charge=delivery_charge_val,
				memo=memo
			)
			# Add products
			product_keys = [k for k in request.POST.keys() if k.startswith('product_')]
			for key in product_keys:
				idx = key.split('_')[1]
				product_id = request.POST.get(f'product_{idx}')
				quantity = request.POST.get(f'quantity_{idx}')
				if product_id and quantity:
					try:
						product = Product.objects.get(pk=product_id)
						qty = int(quantity)
						if qty > 0:
							ExpenseProduct.objects.create(expense=expense, product=product, quantity=qty)
					except Exception:
						continue
			expense.save()
			return redirect('vendor_summary', name=vendor.name)
		else:
			errors.append('Vendor and date are required.')
	return render(request, 'core/expense_add.html', {
		'vendors': vendors,
		'products': products,
		'errors': errors,
	})

@login_required
def payment_add(request):
	return render(request, 'core/payment_add.html', context)

@login_required
def return_add(request):
	from .models import Return, Vendor, Product
	errors = []
	vendors = Vendor.objects.all()
	products = Product.objects.all()
	if request.method == 'POST':
		vendor_id = request.POST.get('vendor')
		date = request.POST.get('date')
		product_id = request.POST.get('product')
		quantity = request.POST.get('quantity')
		if not vendor_id:
			errors.append('Vendor is required.')
		if not date:
			errors.append('Date is required.')
		if not product_id:
			errors.append('Product is required.')
		if not quantity:
			errors.append('Quantity is required.')
		if errors:
			context = {
				'vendors': vendors,
				'products': products,
				'add_errors': errors,
			}
			if request.headers.get('x-requested-with') == 'XMLHttpRequest':
				from django.template.loader import render_to_string
				modal_html = render_to_string('core/return_add_modal_body.html', context, request=request)
				return JsonResponse({'success': False, 'modal_body': modal_html})
			else:
				return render(request, 'core/vendor_summary.html', context)
		vendor = Vendor.objects.get(pk=vendor_id)
		product = Product.objects.get(pk=product_id)
		qty = int(quantity)
		Return.objects.create(vendor=vendor, product=product, quantity=qty, date=date)
		return redirect('vendor_summary', name=vendor.name)
	context = {'vendors': vendors, 'products': products}
	return render(request, 'core/return_list.html', context)

@login_required
def adjustment_add(request):
	from .models import Adjustment, Vendor
	from django.shortcuts import redirect
	import datetime
	vendors = Vendor.objects.all()
	if request.method == 'POST':
		vendor_id = request.POST.get('vendor')
		amount = request.POST.get('amount')
		note = request.POST.get('memo')
		date = request.POST.get('date') or datetime.date.today().isoformat()
		error = None
		if not vendor_id:
			error = 'Vendor is required.'
		elif not amount:
			error = 'Amount is required.'
		if error:
			return render(request, 'core/adjustment_add.html', {'error': error, 'vendors': vendors})
		vendor = Vendor.objects.get(pk=vendor_id)
		Adjustment.objects.create(vendor=vendor, amount=amount, note=note, date=date)
		return redirect('adjustment_list')
	return render(request, 'core/adjustment_add.html', {'vendors': vendors})

@login_required
def payment_list(request):
	from .models import Payment, Vendor
	payments = Payment.objects.select_related('vendor').all().order_by('-date')
	vendors = Vendor.objects.all()
	return render(request, 'core/payment_list.html', {
		'payments': payments,
		'vendors': vendors,
		'active_menu': 'payments',
	})

@login_required
def return_list(request):
	from .models import Return, Vendor, Product
	returns = Return.objects.select_related('vendor').all().order_by('-date')
	vendors = Vendor.objects.all()
	products = Product.objects.all()
	products_list = list(products.values('id', 'name', 'vendor_id', 'price'))
	return render(request, 'core/return_list.html', {
		'returns': returns,
		'vendors': vendors,
		'products': products_list,
		'active_menu': 'returns',
	})

@login_required
def adjustment_list(request):
	from .models import Vendor
	import datetime
	vendors = Vendor.objects.all()
	today = datetime.date.today().isoformat()
	return render(request, 'core/adjustment_list.html', {'active_menu': 'adjustments', 'vendors': vendors, 'today': today})
from django.http import JsonResponse
from .models import Product

@login_required
def ajax_products_by_vendor(request, vendor_id):
    products = Product.objects.filter(vendor_id=vendor_id)
    products_list = list(products.values('id', 'name', 'price'))
    return JsonResponse({'products': products_list})

@login_required
def vendor_summary(request, name):
	import urllib.parse
	from .models import Vendor, Expense, Payment, Return, Adjustment, Product
	vendor_name = urllib.parse.unquote(name)
	vendor = Vendor.objects.filter(name__iexact=vendor_name).first()
	if not vendor:
		from django.http import Http404
		raise Http404('Vendor not found')
	expenses = Expense.objects.filter(vendor=vendor).order_by('-date')
	payments = Payment.objects.filter(vendor=vendor).order_by('-date')
	returns = Return.objects.filter(vendor=vendor).order_by('-date')
	adjustments = Adjustment.objects.filter(vendor=vendor).order_by('-date')
	products = Product.objects.filter(vendor=vendor)  # Only this vendor's products

	# Handle payment creation from modal
	if request.method == 'POST' and 'amount' in request.POST and 'method' in request.POST:
		from .models import Payment
		date = request.POST.get('date')
		amount = request.POST.get('amount')
		method = request.POST.get('method')
		memo = request.FILES.get('memo')
		errors = []
		if not date:
			errors.append('Date is required.')
		if not amount:
			errors.append('Amount is required.')
		if not method:
			errors.append('Method is required.')
		if not errors:
			Payment.objects.create(vendor=vendor, date=date, amount=amount, method=method, memo=memo if memo else None)
			return redirect('vendor_summary', name=vendor.name)
		else:
			context = {
				'vendor': vendor,
				'expenses': expenses,
				'payments': payments,
				'returns': returns,
				'adjustments': adjustments,
				'products': products,
				'add_errors': errors,
			}
			return render(request, 'core/vendor_summary.html', context)

	# Handle adjustment creation from modal
	if request.method == 'POST' and 'amount' in request.POST and 'note' in request.POST and 'adjustment' in request.POST:
		from .models import Adjustment
		date = request.POST.get('date')
		amount = request.POST.get('amount')
		note = request.POST.get('note')
		errors = []
		if not date:
			errors.append('Date is required.')
		if not amount:
			errors.append('Amount is required.')
		if not errors:
			Adjustment.objects.create(vendor=vendor, date=date, amount=amount, note=note)
			return redirect('vendor_summary', name=vendor.name)
		else:
			context = {
				'vendor': vendor,
				'expenses': expenses,
				'payments': payments,
				'returns': returns,
				'adjustments': adjustments,
				'products': products,
				'add_errors': errors,
			}
			return render(request, 'core/vendor_summary.html', context)

	# Find latest transaction
	latest = None
	latest_type = None
	latest_date = None
	latest_amount = None
	latest_obj = None
	all_tx = []
	for obj in [*expenses, *payments, *returns, *adjustments]:
		all_tx.append((obj.date, obj))
	if all_tx:
		# Sort by date only, not by tuple (date, obj)
		all_tx.sort(key=lambda x: x[0], reverse=True)
		latest_date, latest_obj = all_tx[0]
		if isinstance(latest_obj, Expense):
			latest_type = 'Expense'
			latest_amount = latest_obj.amount
		elif isinstance(latest_obj, Payment):
			latest_type = 'Payment'
			latest_amount = latest_obj.amount
		elif isinstance(latest_obj, Return):
			latest_type = 'Return'
			latest_amount = latest_obj.amount
		elif isinstance(latest_obj, Adjustment):
			latest_type = 'Adjustment'
			latest_amount = latest_obj.amount
		latest = latest_obj

	context = {
		'vendor': vendor,
		'expenses': expenses,
		'payments': payments,
		'returns': returns,
		'adjustments': adjustments,
		'latest_type': latest_type,
		'latest_date': latest_date,
		'latest_amount': latest_amount,
		'latest': latest,
		'products': products,
	}
	return render(request, 'core/vendor_summary.html', context)
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404

@login_required
@require_POST
def return_edit(request, pk):
	from .models import Return, Vendor, Product
	ret = get_object_or_404(Return, pk=pk)
	if request.method == 'POST' and request.POST.get('delete'):
		vendor_name = ret.vendor.name
		ret.delete()
		return redirect('vendor_summary', name=vendor_name)
	vendor_id = request.POST.get('vendor')
	date = request.POST.get('date')
	product_id = request.POST.get('product')
	quantity = request.POST.get('quantity')
	errors = []
	if not vendor_id:
		errors.append('Vendor is required.')
	if not date:
		errors.append('Date is required.')
	if not product_id:
		errors.append('Product is required.')
	if not quantity:
		errors.append('Quantity is required.')
	if errors:
		vendor_obj = None
		if vendor_id:
			try:
				vendor_obj = Vendor.objects.get(pk=vendor_id)
			except Vendor.DoesNotExist:
				vendor_obj = None
		products = Product.objects.all()
		context = {
			'vendor': vendor_obj,
			'vendors': Vendor.objects.all(),
			'products': products,
			'add_errors': errors,
		}
		return render(request, 'core/vendor_summary.html', context)
	ret.vendor = Vendor.objects.get(pk=vendor_id)
	ret.date = date
	ret.product = Product.objects.get(pk=product_id)
	ret.quantity = int(quantity)
	ret.save()
	return redirect('vendor_summary', name=ret.vendor.name)

@login_required
@require_POST
def return_delete(request, pk):
    from .models import Return
    ret = get_object_or_404(Return, pk=pk)
    vendor_name = ret.vendor.name
    ret.delete()
    return redirect('vendor_summary', name=vendor_name)

@login_required
def sidebar_test(request):
    return render(request, 'core/sidebar_test.html')
