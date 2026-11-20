import json
from django.conf import settings
from django.db import models
from django.utils import timezone


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stride_profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=12, blank=True)

    def __str__(self):
        return f"Profile - {self.user.email or self.user.username}"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('running', 'Running Shoes'),
        ('sneakers', 'Sneakers'),
        ('casual', 'Casual Shoes'),
        ('slippers', 'Slippers & Chappal'),
        ('sandals', 'Sandals'),
        ('formal', 'Formal Shoes'),
    ]

    name = models.CharField(max_length=200)
    brand_tag = models.CharField(max_length=80, default='Stride Originals')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='running')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sizes = models.CharField(max_length=120, default='UK 6, UK 7, UK 8, UK 9, UK 10')
    size_stock_json = models.TextField(blank=True, default='')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="Optional studio footwear image URL")
    stock = models.PositiveIntegerField(default=15)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_size_stock_dict(self):
        size_list = [s.strip() for s in (self.sizes or '').split(',') if s.strip()]
        if self.size_stock_json:
            try:
                parsed = json.loads(self.size_stock_json)
                if isinstance(parsed, dict):
                    return {k: max(0, int(v)) for k, v in parsed.items()}
            except (ValueError, TypeError):
                pass
        if not size_list:
            return {}
        each = self.stock // len(size_list)
        rem = self.stock % len(size_list)
        mapping = {}
        for idx, sz in enumerate(size_list):
            mapping[sz] = each + (1 if idx < rem else 0)
        return mapping

    def set_size_stock_dict(self, mapping):
        clean = {str(k): max(0, int(v)) for k, v in mapping.items()}
        self.size_stock_json = json.dumps(clean)
        self.stock = sum(clean.values())

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url or ''

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    @property
    def avg_rating(self):
        revs = self.reviews.all()
        if not revs:
            return 4.8
        return round(sum(r.rating for r in revs) / len(revs), 1)

    @property
    def review_count(self):
        return self.reviews.count()


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=120)
    fit_feedback = models.CharField(max_length=60, default='True to Size')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer_name} - {self.rating}★ ({self.product.name})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=25)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=200, default='Footwear Inquiry')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Order(models.Model):
    PAYMENT_METHODS = [
        ('ONLINE', 'Online (UPI / Card / NetBanking)'),
        ('COD', 'Cash on Delivery'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stride_orders')
    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=12)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='ONLINE')
    coupon_code = models.CharField(max_length=40, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=120, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')

    cancel_reason = models.CharField(max_length=255, blank=True)
    exchange_requested = models.BooleanField(default=False)
    exchange_size = models.CharField(max_length=30, blank=True)
    exchange_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} (₹{self.total_amount})"

    @property
    def can_cancel(self):
        return self.status in ('Pending', 'Confirmed')

    @property
    def can_exchange(self):
        if self.status == 'Cancelled':
            return False
        return (timezone.now() - self.created_at).days <= 7


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    selected_size = models.CharField(max_length=30, default='UK 8')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} ({self.selected_size}) x {self.quantity}"