from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.db.models import F, Sum
from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
#=============user model manager==================
class UserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, role='CUSTOMER'):
        if not email:
            raise ValueError("Email is required")

        user = self.model(
            email=self.normalize_email(email),
            phone=phone,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password):
        user = self.create_user(email, phone, password, role='ADMIN')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user



class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.otp}"





class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('SERVICEMAN', 'Serviceman'),
        ('VENDOR', 'Vendor'),
        ('ADMIN', 'Admin'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return self.email



class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    default_address = models.TextField(blank=True, null=True)
    default_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    default_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    profile_image = CloudinaryField(
        'image',
        folder='home_fixer/customers/',
        null=True,
        blank=True
    )
#---------serviceman profile changes start here------------------#

class ServicemanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_online = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    current_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    current_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    # 🔵 LIVE LOCATION (NEW)
    live_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    live_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    experience_years = models.IntegerField(default=0)

    # ✅ NEW: Visiting Charges
    visiting_charge = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
)

    # ✅ NEW: Skills (stored as JSON list)
    skills = models.JSONField(default=list, blank=True)

    average_rating = models.FloatField(default=0.0)

    # ✅ Bank Details
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    # ✅ Profile Image
    profile_image = CloudinaryField(
        'image',
        folder='home_fixer/servicemen/',
        null=True,
        blank=True
    )

    # ✅ KYC Document Image Upload (Cloudinary Image)
    kyc_document = CloudinaryField(
        'image',
        folder='home_fixer/servicemen/kyc/',
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # Auto-update visiting_charge based on the primary skill (first skill in list)
        if self.skills and len(self.skills) > 0:
            from .models import Category
            first_skill = self.skills[0]
            category = Category.objects.filter(name__iexact=first_skill, category_type="SERVICE").first()
            if category:
                # Update visiting_charge to match the category's charge
                self.visiting_charge = category.visiting_charge
        
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'is_approved', 'is_available']),
        ]

class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_approved = models.BooleanField(default=False)  # ✅ NEW FIELD
    # ========================
    # BUSINESS DETAILS
    # ========================
    business_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True, null=True)

    contact_number = models.CharField(max_length=20, blank=True, null=True)
    business_email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)   # ✅ ADD THIS
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)

    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    full_address = models.TextField(blank=True, null=True)

    store_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    store_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    # ========================
    # BANK DETAILS
    # ========================
    account_holder_name = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    # ========================
    # DOCUMENTS (Cloudinary)
    # ========================
    gst_certificate = CloudinaryField(
        'file',
        folder='home_fixer/vendor_documents/gst/',
        null=True,
        blank=True
    )

    store_registration = CloudinaryField(
        'file',
        folder='home_fixer/vendor_documents/store_registration/',
        null=True,
        blank=True
    )

    id_proof = CloudinaryField(
        'file',
        folder='home_fixer/vendor_documents/id_proof/',
        null=True,
        blank=True
    )

    # ========================
    # PROFILE IMAGE
    # ========================
    profile_image = CloudinaryField(
        'image',
        folder='home_fixer/vendors/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name


class Category(models.Model):
    TYPE_CHOICES = (
        ("SERVICE", "Service"),
        ("PRODUCT", "Product"),
    )

    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='children',
        help_text="Select a parent category if this is a subcategory."
    )
    visiting_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    is_trending = models.BooleanField(default=False)
    trending_order = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['is_trending', 'trending_order']),
            models.Index(fields=['category_type']),
        ]

    def save(self, *args, **kwargs):
        is_existing = self.pk is not None
        old_charge = None
        if is_existing:
            try:
                old_category = Category.objects.get(pk=self.pk)
                old_charge = old_category.visiting_charge
            except Category.DoesNotExist:
                pass
            
        super().save(*args, **kwargs)
        
        # If visiting charge changed (or new category), update servicemen who have this as their primary skill
        if self.category_type == "SERVICE":
            if (is_existing and old_charge != self.visiting_charge) or not is_existing:
                from .models import ServicemanProfile
                # Find all servicemen where this category is their primary skill
                for profile in ServicemanProfile.objects.all():
                    if profile.skills and len(profile.skills) > 0:
                        if profile.skills[0].lower() == self.name.lower():
                            profile.visiting_charge = self.visiting_charge
                            profile.save(update_fields=['visiting_charge'])

    def __str__(self):
        return f"{self.name} ({self.category_type})"





class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.name

class Serviceman(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_active = models.BooleanField(default=True)
#End of Changes#



class ServicemanOffering(models.Model):
    serviceman = models.ForeignKey(ServicemanProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Booking(models.Model):

    SERVICE_TYPE_CHOICES = [
        ("VISITING", "Visiting"),
        ("VISITING_SERVICE", "Visiting + Service"),
    ]

    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial Paid'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    customer = models.ForeignKey(
        "CustomerProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True   # 🔥 IMPORTANT
    )

    serviceman = models.ForeignKey(
        "ServicemanProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True   # 🔥 IMPORTANT
    )

    scheduled_date = models.DateField(db_index=True)
    scheduled_time = models.TimeField()

    booking_address = models.TextField(blank=True, null=True)
    booking_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    booking_long = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    problem_title = models.CharField(max_length=255)
    problem_description = models.TextField(blank=True, null=True)

    image_urls = models.JSONField(default=list, blank=True)

    services = models.ManyToManyField("Service", blank=True)

    service_type = models.CharField(
        max_length=30,
        choices=SERVICE_TYPE_CHOICES,
        default="VISITING",
        db_index=True
    )

    visiting_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)

    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING_PAYMENT',
        db_index=True   # 🔥 FILTER USE
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # 🔥 SORT USE
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['serviceman', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_status']),
        ]

    # 🔥 SERVICE TYPE UPDATE
    def update_service_type(self):
        has_items = False
        if self.pk:
            has_items = self.items.filter(approval_status="APPROVED").exists()
        if self.service_charge > 0 or has_items:
            self.service_type = "VISITING_SERVICE"
        else:
            self.service_type = "VISITING"

    # 🔥 TOTAL COST UPDATE (OPTIMIZED)
    def update_total_cost(self):
        if self.pk:
            product_total = self.items.filter(
                approval_status="APPROVED"
            ).aggregate(total=Sum(F("quantity") * F("product_price")))["total"] or 0
        else:
            product_total = 0

        self.total_cost = (
            self.visiting_charge +
            self.service_charge +
            self.platform_fee +
            product_total
        )

    def save(self, *args, **kwargs):
        self.update_service_type()
        self.update_total_cost()
        super().save(*args, **kwargs)

    def mark_as_completed(self):
        """
        Centralized logic to complete a booking.
        - Updates status to COMPLETED
        - Updates payment_status to PAID
        - Marks serviceman as available
        - Credits serviceman wallet
        """
        from django.db import transaction as db_transaction
        from .models import Wallet, Transaction as WalletTransaction
        
        with db_transaction.atomic():
            if self.status != "COMPLETED":
                self.status = "COMPLETED"
                self.payment_status = "PAID"
                self.save(update_fields=["status", "payment_status"])

            if self.serviceman:
                self.serviceman.is_available = True
                self.serviceman.save(update_fields=["is_available"])

                # Credit serviceman wallet with service charge + visiting charge
                # Ensure we don't double credit
                if not WalletTransaction.objects.filter(booking=self, type="CREDIT", wallet__user=self.serviceman.user).exists():
                    amount = self.service_charge + self.visiting_charge
                    if amount > 0:
                        wallet, _ = Wallet.objects.get_or_create(user=self.serviceman.user)
                        wallet.balance += amount
                        wallet.save(update_fields=["balance"])

                        WalletTransaction.objects.create(
                            wallet=wallet,
                            booking=self,
                            type="CREDIT",
                            amount=amount,
                            description=f"Earnings for Booking #{self.id}"
                        )

    def __str__(self):
        return f"Booking #{self.id}"



class BookingImage(models.Model):

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = CloudinaryField(
        'image',
        folder='home_fixer/bookings/',
        null=True,
        blank=True
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Booking {self.booking.id}"





class Product(models.Model):
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    min_stock_alert = models.IntegerField(default=5)
    image = CloudinaryField(
    'image',
    folder='home_fixer/products/',
    null=True,
    blank=True
)

    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['-created_at']),
        ]

class BookingItem(models.Model):

    booking = models.ForeignKey("Booking", on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey("Product", null=True, on_delete=models.SET_NULL)

    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.URLField(null=True, blank=True)

    product_data = models.JSONField(default=dict)

    quantity = models.PositiveIntegerField(default=1)

    APPROVAL_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("AUTO_REJECTED", "Auto Rejected"),
    ]

    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default="PENDING")

    is_ordered = models.BooleanField(default=False)

    @property
    def total_price(self):
        return self.quantity * self.product_price

    # 🔥 OPTIMIZED SAVE
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from django.db.models import Sum, F

        if self.booking:
            product_total = self.booking.items.filter(
                approval_status="APPROVED"
            ).aggregate(
            total=Sum(F('quantity') * F('product_price'))
            )['total'] or 0

            total_cost = (
                self.booking.visiting_charge +
                self.booking.service_charge +
                self.booking.platform_fee +
                product_total
            )

            service_type = "VISITING_SERVICE" if product_total > 0 or self.booking.service_charge > 0 else "VISITING"

            Booking.objects.filter(id=self.booking.id).update(
                total_cost=total_cost,
                service_type=service_type
            )    

class MaterialOrder(models.Model):

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('VENDOR_ACCEPTED', 'Vendor Accepted'),
        ('COLLECTED', 'Collected by Serviceman'),  # 🔥 NEW
        ('DELIVERED', 'Delivered'),
        ('AUTO_REJECTED', 'Auto Rejected'),
        ('FULFILLED', 'Fulfilled'),
    ]

    tracking_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    booking = models.ForeignKey(
        Booking,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="material_orders"
    )

    serviceman = models.ForeignKey(
        ServicemanProfile,
        on_delete=models.CASCADE,
        related_name="material_orders"
    )

    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="material_orders"
    )

    is_collected = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )

    customer_approve = models.BooleanField(default=False)

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    assigned_vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders"
)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_auto_reject(self):
        from django.utils import timezone
        import datetime
        if self.status == 'REQUESTED':
            if timezone.now() > self.created_at + datetime.timedelta(minutes=2):
                self.status = 'AUTO_REJECTED'
                self.save(update_fields=['status'])
                
                # Auto-reject the booking items tied to this order
                for item in self.booking.items.filter(product__vendor=self.vendor, approval_status="APPROVED"):
                    item.approval_status = "AUTO_REJECTED"
                    item.save(update_fields=["approval_status"])

    def save(self, *args, **kwargs):
        import uuid
        if not self.tracking_code:
            self.tracking_code = f"TRK-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    
    def update_total_cost(self):
    
        approved_total = self.items.aggregate(
        total=Sum(F("quantity") * F("price_at_order"))
    )["total"] or 0

        self.total_cost = approved_total
        self.save(update_fields=["total_cost"])
    
    def __str__(self):
        return f"Order #{self.id}"


class MaterialOrderItem(models.Model):
    order = models.ForeignKey(
        MaterialOrder,
        on_delete=models.CASCADE,
        related_name="items"   # ✅ FIXED
    )

    product = models.ForeignKey(Product, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField()   # ✅ FIXED

    price_at_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):
        order = self.order

        # ✅ Check if update
        if self.pk:
            old = MaterialOrderItem.objects.get(pk=self.pk)

            if (
                old.quantity != self.quantity or
                old.price_at_order != self.price_at_order or
                old.product_id != self.product_id
            ):
                # 🔥 Reset approval
                if order.customer_approve:
                    order.customer_approve = False
                    order.status = "REQUESTED"
                    order.save(update_fields=["customer_approve", "status"])

        super().save(*args, **kwargs)

        # 🔥 AUTO UPDATE TOTAL COST
        order.update_total_cost()


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)



class Transaction(models.Model):
    TYPE_CHOICES = [('CREDIT','Credit'),('DEBIT','Debit')]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, blank=True)
    admin_payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    upi_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Withdrawal #{self.id} - {self.user.email} - {self.amount}"




class Review(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, related_name='given_reviews', on_delete=models.CASCADE)
    reviewee = models.ForeignKey(User, related_name='received_reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



#===========================PAYMENT MODEL STARTS HERE===========================#
from django.db import models
from django.utils import timezone

class Payment(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ]

    METHOD_CHOICES = [
        ("UPI", "UPI"),
        ("CARD", "Card"),
        ("NETBANKING", "Net Banking"),
        ("WALLET", "Wallet"),
    ]

    GATEWAY_CHOICES = [
        ("RAZORPAY", "Razorpay"),
        ("STRIPE", "Stripe"),
    ]

    PAYMENT_TYPE_CHOICES = [
        ("VISITING", "Visiting Payment"),
        ("FINAL", "Final Payment"),
    ]

    booking = models.ForeignKey(
        "Booking",
        on_delete=models.CASCADE,
        related_name="payments"
    )

    customer = models.ForeignKey(
        "CustomerProfile",
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default="VISITING"
    )

    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        null=True,
        blank=True
    )

    gateway = models.CharField(
        max_length=20,
        choices=GATEWAY_CHOICES,
        default="RAZORPAY"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    gateway_order_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_payment_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_signature = models.TextField(null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)


    # 🔥 MAIN LOGIC
    def save(self, *args, **kwargs):
        is_paid_before = False

        if self.pk:
            old = Payment.objects.get(pk=self.pk)
            is_paid_before = old.status == "PAID"

        # 🔥 AUTO AMOUNT CALCULATION
        if not self.amount or self.amount == 0:

            # ✅ VISITING PAYMENT
            if self.payment_type in ("VISITING", "VISITING_SERVICE"):
                base_visiting = self.booking.serviceman.visiting_charge
                self.amount = base_visiting + self.booking.platform_fee

                # Safely update the booking record to match
                if self.booking.visiting_charge != base_visiting:
                    self.booking.visiting_charge = base_visiting
                    self.booking.save(update_fields=["visiting_charge", "total_cost"])

            # ✅ FINAL PAYMENT
            elif self.payment_type == "FINAL":
                from django.db.models import Sum, F

                product_total = self.booking.items.filter(
                    approval_status="APPROVED"
                ).aggregate(
                    total=Sum(F('quantity') * F('product_price'))
                )['total'] or 0
                self.amount = (
                    self.booking.service_charge +
                    product_total
                )

        # 🔥 SET PAID TIME
        if self.status == "PAID" and not self.paid_at:
            self.paid_at = timezone.now()

        super().save(*args, **kwargs)

        # 🔥 UPDATE BOOKING STATUS
        if self.status == "PAID" and not is_paid_before:

            # ✅ VISITING PAID
            if self.payment_type in ("VISITING", "VISITING_SERVICE"):
                self.booking.payment_status = "PARTIAL"
                self.booking.status = "PENDING"
                self.booking.save(update_fields=["payment_status", "status"])
                
                # Trigger the 90s/270s reassignment flow
                try:
                    from .reassign_logic import start_booking_assignment_flow
                    start_booking_assignment_flow(self.booking.id)
                except Exception as e:
                    pass

            # ✅ FINAL PAID
            elif self.payment_type == "FINAL":
                self.booking.mark_as_completed()

    def __str__(self):
        return f"{self.payment_type} - {self.gateway} Payment #{self.id}"
    
    
User = get_user_model()

class OrderItem(models.Model):

    booking = models.ForeignKey(
        Booking,
        related_name='order_items',
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # ❌ REMOVE vendor field

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=[
            ('requested', 'Requested'),
            ('approved', 'Approved'),
            ('auto_rejected', 'Auto Rejected'),
            ('delivered', 'Delivered'),
        ],
        default='requested'
    )

    created_at = models.DateTimeField(auto_now_add=True)


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"

class PlatformSettings(models.Model):
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)

    class Meta:
        verbose_name_plural = 'Platform Settings'

    def __str__(self):
        return f'Platform Settings (Fee: {self.platform_fee})'
