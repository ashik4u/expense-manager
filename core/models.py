from django.db import models


class Vendor(models.Model):
	name = models.CharField(max_length=100)
	contact = models.CharField(max_length=100, blank=True)
	opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

	def __str__(self):
		return self.name


class Product(models.Model):
	name = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')

	def __str__(self):
		return self.name




class Expense(models.Model):
	vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='expenses')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	memo = models.FileField(upload_to='memos/', blank=True, null=True)
	date = models.DateField()

	def subtotal(self):
		return sum([ep.product.price * ep.quantity for ep in self.expense_products.all()])

	def save(self, *args, **kwargs):
		# On first save, set amount to 0 to satisfy NOT NULL constraint
		if self.pk is None:
			self.amount = 0
			super().save(*args, **kwargs)
			self.amount = self.subtotal() + self.delivery_charge
			super().save(update_fields=["amount"])
		else:
			self.amount = self.subtotal() + self.delivery_charge
			super().save(*args, **kwargs)

	def __str__(self):
		return f"Expense {self.id} - {self.vendor.name} - {self.amount} on {self.date}"


class ExpenseProduct(models.Model):
	expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='expense_products')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)

	def __str__(self):
		return f"{self.product.name} x {self.quantity} for Expense {self.expense.id}"


class Payment(models.Model):
	vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payments')
	PAYMENT_METHOD_CHOICES = [
		('Bank', 'Bank'),
		('Cash', 'Cash'),
		('bKash', 'bKash'),
	]
	method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	date = models.DateField()
	memo = models.FileField(upload_to='payment_memos/', blank=True, null=True)

	def __str__(self):
		return f"Payment {self.id} - {self.vendor.name} - {self.amount} on {self.date}"


class Return(models.Model):
		vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='returns')
		product = models.ForeignKey(Product, on_delete=models.CASCADE)
		quantity = models.PositiveIntegerField(default=1)
		amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
		date = models.DateField()

		def save(self, *args, **kwargs):
			if self.product and self.quantity:
				self.amount = self.product.price * self.quantity
			super().save(*args, **kwargs)

		def __str__(self):
			return f"Return {self.id} - {self.vendor.name} - {self.amount} on {self.date}"


class Adjustment(models.Model):
	vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='adjustments')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	note = models.CharField(max_length=200, blank=True)
	date = models.DateField()

	def __str__(self):
		return f"Adjustment {self.id} - {self.vendor.name} - {self.amount} on {self.date}"
