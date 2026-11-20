from django.contrib import admin
from .models import ContactMessage, CustomerProfile, Order, OrderItem, Product, Review


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'city', 'pincode')
    search_fields = ('user__email', 'user__username', 'phone', 'city')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'original_price', 'stock', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'brand_tag', 'sizes')
    list_editable = ('price', 'original_price', 'stock', 'is_featured')
    inlines = [ReviewInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'reviewer_name', 'fit_feedback', 'rating', 'created_at')
    list_filter = ('rating', 'fit_feedback', 'created_at')
    search_fields = ('reviewer_name', 'comment', 'product__name')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'subject', 'created_at')
    search_fields = ('name', 'phone', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'selected_size', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'phone', 'total_amount', 'payment_method',
        'is_paid', 'status', 'exchange_requested', 'exchange_size', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'is_paid', 'exchange_requested', 'created_at')
    search_fields = ('id', 'customer_name', 'phone', 'razorpay_payment_id')
    list_editable = ('status', 'is_paid')
    inlines = [OrderItemInline]