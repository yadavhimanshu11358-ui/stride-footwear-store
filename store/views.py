import json
import logging
from decimal import Decimal
import razorpay
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import ContactMessage, CustomerProfile, Order, OrderItem, Product, Review

logger = logging.getLogger(__name__)


def _notify_events(subject, body, customer_email=''):
    logger.info("STRIDE NOTIFICATION | %s | %s", subject, body.replace('\n', ' | '))
    owner_email = getattr(settings, 'STORE_NOTIFY_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')
    recipients = []
    if owner_email:
        recipients.append(owner_email)
    if customer_email and customer_email not in recipients:
        recipients.append(customer_email)
    if recipients and getattr(settings, 'EMAIL_HOST', ''):
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'care@stridefootwear.in'),
                recipient_list=recipients,
                fail_silently=True,
            )
        except Exception as exc:
            logger.warning("Email notification skipped/failed: %s", exc)


def _get_profile_payload(user):
    if not user or not user.is_authenticated:
        return None
    prof, _ = CustomerProfile.objects.get_or_create(user=user)
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    return {
        'full_name': full_name,
        'email': user.email,
        'phone': prof.phone,
        'address': prof.address,
        'city': prof.city,
        'pincode': prof.pincode,
    }


def _serialize_order(order):
    return {
        'order_id': order.id,
        'id': order.id,
        'customer_name': order.customer_name,
        'phone': order.phone,
        'address': f"{order.address}, {order.city} - {order.pincode}",
        'total_amount': str(order.total_amount),
        'discount': str(order.discount_amount),
        'payment_method': order.get_payment_method_display(),
        'is_paid': order.is_paid,
        'status': order.status,
        'can_cancel': order.can_cancel,
        'can_exchange': order.can_exchange,
        'exchange_requested': order.exchange_requested,
        'exchange_size': order.exchange_size,
        'date': timezone.localtime(order.created_at).strftime('%d %b %Y, %I:%M %p'),
        'items': [
            {'name': i.product_name, 'size': i.selected_size, 'qty': i.quantity, 'price': str(i.price)}
            for i in order.items.all()
        ],
    }


def home(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all').strip()
    sort = request.GET.get('sort', 'latest').strip()
    price_band = request.GET.get('price', 'all').strip()
    min_rating = request.GET.get('rating', '0').strip()
    discount_only = request.GET.get('discount', '') == '1'
    show_all = request.GET.get('show_all', '') == '1'

    products = list(Product.objects.prefetch_related('reviews').all())

    if category and category != 'all':
        products = [p for p in products if p.category == category]

    if query:
        ql = query.lower()
        products = [
            p for p in products
            if ql in p.name.lower()
            or ql in p.description.lower()
            or ql in p.brand_tag.lower()
            or ql in p.sizes.lower()
        ]

    if price_band == 'under_500':
        products = [p for p in products if p.price < Decimal('500.00')]
    elif price_band == '500_1500':
        products = [p for p in products if Decimal('500.00') <= p.price <= Decimal('1500.00')]
    elif price_band == '1500_plus':
        products = [p for p in products if p.price > Decimal('1500.00')]

    if min_rating == '4':
        products = [p for p in products if float(p.avg_rating) >= 4.0]

    if discount_only:
        products = [p for p in products if p.discount_percent > 0]

    if sort == 'price_asc':
        products.sort(key=lambda p: p.price)
    elif sort == 'price_desc':
        products.sort(key=lambda p: p.price, reverse=True)
    else:
        products.sort(key=lambda p: (not p.is_featured, -p.id))

    total_matching = len(products)
    per_page = total_matching if show_all and total_matching > 0 else 12
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    recent_reviews = Review.objects.select_related('product').order_by('-created_at')[:6]
    prof_payload = _get_profile_payload(request.user)

    return render(request, 'store/index.html', {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'total_matching': total_matching,
        'show_all': show_all,
        'categories': Product.CATEGORY_CHOICES,
        'selected_category': category,
        'search_query': query,
        'selected_sort': sort,
        'selected_price': price_band,
        'selected_rating': min_rating,
        'discount_only': discount_only,
        'recent_reviews': recent_reviews,
        'profile_data': json.dumps(prof_payload) if prof_payload else '',
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    })


def live_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})

    qs = Product.objects.filter(
        Q(name__icontains=q)
        | Q(brand_tag__icontains=q)
        | Q(category__icontains=q)
        | Q(description__icontains=q)
    ).order_by('-is_featured', 'price')[:8]

    results = [
        {
            'id': str(p.id),
            'name': p.name,
            'brand': p.brand_tag,
            'category': p.get_category_display(),
            'price': str(p.price),
            'original_price': str(p.original_price) if p.original_price else '',
            'image': p.display_image,
            'stock': p.stock,
        }
        for p in qs
    ]
    return JsonResponse({'results': results})


@require_POST
def auth_register(request):
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')

        if not full_name or not email or len(password) < 6:
            return JsonResponse({'error': 'Name, valid email, and 6+ character password are required.'}, status=400)
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'An account with this email already exists. Please sign in.'}, status=400)

        parts = full_name.split(' ', 1)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else '',
        )
        CustomerProfile.objects.create(user=user, phone=phone)
        login(request, user)
        return JsonResponse({'status': 'ok', 'message': 'Account created successfully!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def auth_login(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        user = authenticate(request, username=email, password=password)
        if not user:
            return JsonResponse({'error': 'Invalid email or password.'}, status=400)
        login(request, user)
        return JsonResponse({'status': 'ok', 'message': 'Signed in!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def auth_logout(request):
    logout(request)
    return JsonResponse({'status': 'ok'})


@require_POST
def save_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please sign in first.'}, status=401)
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name', '').strip()
        if full_name:
            parts = full_name.split(' ', 1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts) > 1 else ''
            request.user.save()

        prof, _ = CustomerProfile.objects.get_or_create(user=request.user)
        prof.phone = data.get('phone', '').strip()
        prof.address = data.get('address', '').strip()
        prof.city = data.get('city', '').strip()
        prof.pincode = data.get('pincode', '').strip()
        prof.save()
        return JsonResponse({'status': 'ok', 'message': 'Saved address updated!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def add_review(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        reviewer_name = data.get('reviewer_name', '').strip()
        fit_feedback = data.get('fit_feedback', 'True to Size').strip() or 'True to Size'
        rating = int(data.get('rating', 5))
        comment = data.get('comment', '').strip()

        if not reviewer_name or not comment:
            return JsonResponse({'error': 'Please enter your name and review.'}, status=400)
        if rating < 1 or rating > 5:
            rating = 5

        product = Product.objects.get(id=product_id)
        review = Review.objects.create(
            product=product,
            reviewer_name=reviewer_name,
            fit_feedback=fit_feedback,
            rating=rating,
            comment=comment,
        )
        return JsonResponse({
            'id': review.id,
            'reviewer_name': review.reviewer_name,
            'fit_feedback': review.fit_feedback,
            'rating': review.rating,
            'comment': review.comment,
            'avg_rating': product.avg_rating,
            'review_count': product.review_count,
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def send_contact(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', 'Footwear Inquiry').strip()
        message = data.get('message', '').strip()

        if not name or not phone or not message:
            return JsonResponse({'error': 'Name, phone, and message are required.'}, status=400)

        ContactMessage.objects.create(
            name=name,
            phone=phone,
            email=email,
            subject=subject,
            message=message,
        )
        _notify_events(
            f"STRIDE Inquiry: {subject} from {name}",
            f"Name: {name}\nPhone: {phone}\nEmail: {email}\nMessage: {message}",
            customer_email=email,
        )
        return JsonResponse({'status': 'ok', 'message': 'Thank you! Our store specialist will reach out shortly.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def create_order(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        if not items:
            return JsonResponse({'error': 'Your cart is empty.'}, status=400)

        customer_name = data.get('customer_name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        pincode = data.get('pincode', '').strip()
        payment_method = data.get('payment_method', 'COD')
        coupon_code = data.get('coupon_code', '').strip().upper()

        if not all([customer_name, phone, address, city, pincode]):
            return JsonResponse({'error': 'Please fill all delivery details.'}, status=400)

        with transaction.atomic():
            subtotal = Decimal('0.00')
            validated_items = []

            for entry in items:
                product = Product.objects.select_for_update().get(id=entry['id'])
                qty = int(entry['qty'])
                size = str(entry.get('size') or 'UK 8').strip()
                if qty <= 0:
                    continue

                size_map = product.get_size_stock_dict()
                sz_avail = size_map.get(size, product.stock)
                if sz_avail < qty:
                    return JsonResponse(
                        {'error': f'Only {sz_avail} pair(s) available in {size} for {product.name}.'},
                        status=400,
                    )

                subtotal += product.price * qty
                validated_items.append((product, qty, size, size_map))

            discount = Decimal('0.00')
            if coupon_code == 'STRIDE10':
                discount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
            elif coupon_code == 'FIRST150' and subtotal >= Decimal('999.00'):
                discount = Decimal('150.00')
            else:
                coupon_code = ''

            discounted_sub = max(Decimal('0.00'), subtotal - discount)
            shipping = Decimal('0.00') if discounted_sub >= Decimal('599.00') else Decimal('59.00')
            total_amount = discounted_sub + shipping

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                customer_name=customer_name,
                phone=phone,
                email=email,
                address=address,
                city=city,
                pincode=pincode,
                payment_method=payment_method,
                coupon_code=coupon_code,
                discount_amount=discount,
                total_amount=total_amount,
                status='Confirmed' if payment_method == 'COD' else 'Pending',
            )

            receipt_items = []
            for product, qty, size, size_map in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    selected_size=size,
                    price=product.price,
                    quantity=qty,
                )
                if size in size_map:
                    size_map[size] = max(0, size_map[size] - qty)
                    product.set_size_stock_dict(size_map)
                else:
                    product.stock = max(0, product.stock - qty)
                product.save()
                receipt_items.append(f"{product.name} ({size}) x{qty}")

            if request.user.is_authenticated:
                prof, _ = CustomerProfile.objects.get_or_create(user=request.user)
                prof.phone = phone or prof.phone
                prof.address = address or prof.address
                prof.city = city or prof.city
                prof.pincode = pincode or prof.pincode
                prof.save()

            receipt = {
                'order_id': order.id,
                'customer_name': order.customer_name,
                'phone': order.phone,
                'address': f"{order.address}, {order.city} - {order.pincode}",
                'payment_method': order.get_payment_method_display(),
                'total_amount': str(order.total_amount),
                'discount': str(order.discount_amount),
                'items': receipt_items,
            }

            if payment_method == 'ONLINE':
                if 'YourKeyHere' in settings.RAZORPAY_KEY_ID:
                    return JsonResponse({
                        'error': 'Razorpay keys are not configured yet. Select Cash on Delivery (COD) to complete your order now.'
                    }, status=400)

                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                rzp_order = client.order.create({
                    'amount': int(total_amount * 100),
                    'currency': 'INR',
                    'payment_capture': '1',
                })
                order.razorpay_order_id = rzp_order['id']
                order.save()

                return JsonResponse({
                    'order_id': order.id,
                    'razorpay_order_id': rzp_order['id'],
                    'amount': int(total_amount * 100),
                    'currency': 'INR',
                    'receipt': receipt,
                })

            _notify_events(
                f"STRIDE Order Confirmed #{order.id} (COD)",
                f"Customer: {order.customer_name} ({order.phone})\nTotal: ₹{order.total_amount}\nItems: {', '.join(receipt_items)}\nAddress: {order.address}, {order.city} - {order.pincode}",
                customer_email=order.email,
            )

            return JsonResponse({
                'order_id': order.id,
                'receipt': receipt,
                'message': 'Order placed successfully!',
            })

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def verify_payment(request):
    try:
        data = json.loads(request.body)
        order = Order.objects.get(id=data['order_id'])

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature'],
        })

        order.is_paid = True
        order.status = 'Confirmed'
        order.razorpay_payment_id = data['razorpay_payment_id']
        order.save()

        item_list = [f"{i.product_name} ({i.selected_size}) x{i.quantity}" for i in order.items.all()]
        _notify_events(
            f"STRIDE Online Payment Paid — Order #{order.id}",
            f"Customer: {order.customer_name} ({order.phone})\nPaid: ₹{order.total_amount}\nPayment ID: {order.razorpay_payment_id}\nItems: {', '.join(item_list)}",
            customer_email=order.email,
        )

        return JsonResponse({'status': 'success', 'order_id': order.id})
    except Exception as e:
        return JsonResponse({'error': 'Payment verification failed: ' + str(e)}, status=400)


def track_orders(request):
    phone = request.GET.get('phone', '').strip()
    if request.user.is_authenticated and not phone:
        qs = Order.objects.filter(
            Q(user=request.user) | Q(email__iexact=request.user.email)
        ).order_by('-created_at')[:15]
    elif phone:
        qs = Order.objects.filter(phone=phone).order_by('-created_at')[:15]
    else:
        return JsonResponse({'orders': []})

    return JsonResponse({'orders': [_serialize_order(o) for o in qs]})


@require_POST
def cancel_order(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        reason = data.get('reason', '').strip() or 'Cancelled by customer'

        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            if order.status not in ('Pending', 'Confirmed'):
                return JsonResponse({'error': 'Only Pending or Confirmed orders can be cancelled.'}, status=400)

            for item in order.items.select_related('product').all():
                if item.product:
                    p = Product.objects.select_for_update().get(id=item.product.id)
                    smap = p.get_size_stock_dict()
                    if item.selected_size in smap:
                        smap[item.selected_size] += item.quantity
                        p.set_size_stock_dict(smap)
                    else:
                        p.stock += item.quantity
                    p.save()

            order.status = 'Cancelled'
            order.cancel_reason = reason
            order.save()

        _notify_events(
            f"STRIDE Order Cancelled #{order.id}",
            f"Customer: {order.customer_name} ({order.phone})\nReason: {reason}",
            customer_email=order.email,
        )
        return JsonResponse({'status': 'ok', 'order': _serialize_order(order)})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def request_exchange(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_size = data.get('exchange_size', '').strip()
        reason = data.get('reason', '').strip()

        if not new_size:
            return JsonResponse({'error': 'Please select the new UK size for exchange.'}, status=400)

        order = Order.objects.get(id=order_id)
        age_days = (timezone.now() - order.created_at).days
        if age_days > 7:
            return JsonResponse({'error': '7-day size exchange window has expired for this order.'}, status=400)

        order.exchange_requested = True
        order.exchange_size = new_size
        order.exchange_reason = reason or f"Exchange requested for {new_size}"
        order.save()

        _notify_events(
            f"STRIDE 7-Day Size Exchange Request — Order #{order.id}",
            f"Customer: {order.customer_name} ({order.phone})\nNew Size: {new_size}\nReason: {order.exchange_reason}",
            customer_email=order.email,
        )
        return JsonResponse({'status': 'ok', 'order': _serialize_order(order)})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)