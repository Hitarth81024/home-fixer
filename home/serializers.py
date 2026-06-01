
from decimal import Decimal
import cloudinary.uploader
from .utils import delete_cloudinary_image
from rest_framework import serializers
from .models import Payment, User, CustomerProfile, ServicemanProfile, VendorProfile, Booking, BookingItem
import re
from django.contrib.auth import authenticate
from django.db.models import Sum, F
class EmailPasswordLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        data["user"] = user
        return data




#==========Logout Serializer ==========#
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


#==========Otp sent and verification serializers ==========#
class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

#===========Verify OTP Serializer ==========#
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

#===========Complete Registration Serializer ==========#


class CompleteRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True, max_length=255)
    phone = serializers.CharField(
        required=True,
        min_length=10,
        max_length=10
    )
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=["CUSTOMER", "SERVICEMAN", "VENDOR"],
        default="CUSTOMER"
    )

    def validate_phone(self, value):
        if not re.fullmatch(r"\d{10}", value):
            raise serializers.ValidationError("Enter valid 10-digit phone number")

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone already exists")

        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists"
            )
        return value


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)
    phone = serializers.CharField(required=False, max_length=20)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)

    def validate(self, data):
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        from django.conf import settings

        token = data.get("id_token")
        client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)

        try:
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)

            # ID token is valid. Get the user's Google ID information.
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Wrong issuer.')

            data["email"] = idinfo['email']
            data["name"] = idinfo.get('name', '')
            data["google_id"] = idinfo['sub']

        except ValueError:
            # Invalid token
            raise serializers.ValidationError("Invalid Google ID token")

        return data

#===========User Profile Serializer ==========#
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'role',
            'is_verified',
        ]


#===========Customer, Serviceman, Vendor Profile Serializers ==========#

class CustomerAddressSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(default="Default", required=False)
    address = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8)
    is_default = serializers.BooleanField(default=True, required=False)

    def create(self, validated_data):
        request = self.context.get("request")
        profile = request.user.customerprofile
        profile.default_address = validated_data.get("address")
        profile.default_lat = validated_data.get("latitude")
        profile.default_long = validated_data.get("longitude")
        profile.save()
        return {
            "id": request.user.id,
            "title": "Default",
            "address": profile.default_address,
            "latitude": profile.default_lat,
            "longitude": profile.default_long,
            "is_default": True
        }

    def update(self, instance, validated_data):
        request = self.context.get("request")
        profile = request.user.customerprofile
        profile.default_address = validated_data.get("address", profile.default_address)
        profile.default_lat = validated_data.get("latitude", profile.default_lat)
        profile.default_long = validated_data.get("longitude", profile.default_long)
        profile.save()
        return {
            "id": request.user.id,
            "title": "Default",
            "address": profile.default_address,
            "latitude": profile.default_lat,
            "longitude": profile.default_long,
            "is_default": True
        }

class CustomerProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    # User fields
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', max_length=255, required=False)
    phone = serializers.CharField(source='user.phone', min_length=10, max_length=10, required=False)

    class Meta:
        model = CustomerProfile
        fields = [
            'email',
            'name',
            'phone',
            'default_address',
            'default_lat',
            'default_long',
            'profile_image',
            'profile_image_url',
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            if 'name' in user_data:
                user.name = user_data['name']
            if 'phone' in user_data:
                user.phone = user_data['phone']
            user.save()

        new_image = validated_data.get('profile_image')

        if new_image and instance.profile_image:
            delete_cloudinary_image(instance.profile_image)

        return super().update(instance, validated_data)



class ServicemanProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user_id', read_only=True)
    
    # User fields
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', max_length=255, required=False)
    phone = serializers.CharField(source='user.phone', min_length=10, max_length=10, required=False)

    visiting_charge = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    skills = serializers.CharField(
        required=False,
        help_text='Enter skill'
    )
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    # RESTORED kyc_document as writable input
    kyc_document = serializers.ImageField(required=False, write_only=True)
    kyc_document_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ServicemanProfile
        fields = [
            'id',
            'email',
            'name',
            'phone',
            'is_online',
            'is_approved',
            'is_active',
            'is_available',
            'current_lat',
            'current_long',
            'live_lat',
            'live_long',
            'experience_years',
            'visiting_charge',
            'skills',
            'average_rating',
            'profile_image',
            'profile_image_url',
            'kyc_document',
            'kyc_document_url',
            'upi_id',
        ]
        read_only_fields = ['is_approved', 'visiting_charge', 'is_active', 'average_rating']

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def get_kyc_document_url(self, obj):
        if obj.kyc_document:
            return obj.kyc_document.url
        return None


    def validate_skills(self, value):
        if value:
            return [skill.strip() for skill in value.split(',')]
        return []

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            if 'name' in user_data:
                user.name = user_data['name']
            if 'phone' in user_data:
                user.phone = user_data['phone']
            user.save()

        # RESTRICTION: Only allow updating kyc_document if it is NOT SET, or if user is ADMIN
        request = self.context.get('request')
        if 'kyc_document' in validated_data:
            is_admin = request and request.user.role == 'ADMIN'
            is_new_upload = not instance.kyc_document
            
            if not (is_admin or is_new_upload):
                validated_data.pop('kyc_document')

        file_fields = ['profile_image', 'kyc_document']

        for field in file_fields:
            new_file = validated_data.get(field)
            old_file = getattr(instance, field)

            if new_file and old_file:
                delete_cloudinary_image(old_file)

        return super().update(instance, validated_data)



class VendorProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user_id', read_only=True)    

    # User fields
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', max_length=255, required=False)
    phone = serializers.CharField(source='user.phone', min_length=10, max_length=10, required=False)

    # ========= Image Upload =========
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    # ========= Documents Upload (RESTORED) =========
    gst_certificate = serializers.FileField(required=False, write_only=True)
    store_registration = serializers.FileField(required=False, write_only=True)
    id_proof = serializers.FileField(required=False, write_only=True)

    gst_certificate_url = serializers.SerializerMethodField(read_only=True)
    store_registration_url = serializers.SerializerMethodField(read_only=True)
    id_proof_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'email',
            'name',
            'phone',
            'is_approved',
            'is_active',
            # ================= BUSINESS =================
            'business_name',
            'gst_number',
            'contact_number',
            'business_email',
            'opening_time',
            'closing_time',
            'city',
            'state',
            'full_address',
            'store_lat',
            'store_long',

            # ================= BANK =================
            'account_holder_name',
            'bank_name',
            'account_number',
            'ifsc_code',
            'upi_id',

            # ================= IMAGE =================
            'profile_image',
            'profile_image_url',

            # ================= DOCUMENTS =================
            'gst_certificate',
            'store_registration',
            'id_proof',
            'gst_certificate_url',
            'store_registration_url',
            'id_proof_url',
        ]
        read_only_fields = ['is_approved','is_active']  # 🔒 Only admin can change

    # ================= IMAGE URL =================
    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    # ================= DOCUMENT URLS =================
    def get_gst_certificate_url(self, obj):
        if obj.gst_certificate:
            return obj.gst_certificate.url
        return None

    def get_store_registration_url(self, obj):
        if obj.store_registration:
            return obj.store_registration.url
        return None

    def get_id_proof_url(self, obj):
        if obj.id_proof:
            return obj.id_proof.url
        return None


    # ================= SAFE UPDATE (Delete Old Cloudinary Files) =================
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            if 'name' in user_data:
                user.name = user_data['name']
            if 'phone' in user_data:
                user.phone = user_data['phone']
            user.save()

        # RESTRICTION: Only allow updating docs if they are NOT SET, or if user is ADMIN
        request = self.context.get('request')
        doc_fields = ['gst_certificate', 'store_registration', 'id_proof']
        
        for field in doc_fields:
            if field in validated_data:
                is_admin = request and request.user.role == 'ADMIN'
                is_new_upload = not getattr(instance, field)
                
                if not (is_admin or is_new_upload):
                    validated_data.pop(field)

        file_fields = [
            'profile_image',
            'gst_certificate',
            'store_registration',
            'id_proof',
        ]

        for field in file_fields:
            new_file = validated_data.get(field)
            old_file = getattr(instance, field)

            if new_file and old_file:
                delete_cloudinary_image(old_file)

        return super().update(instance, validated_data)





class ProfileResponseSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    profile = serializers.DictField()



class UniversalProfileUpdateSerializer(serializers.Serializer):

    # ===== CUSTOMER =====
    default_address = serializers.CharField(required=False)
    default_lat = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    default_long = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    profile_pic_url = serializers.URLField(required=False)

    # ===== SERVICEMAN =====
    is_online = serializers.BooleanField(required=False)
    current_lat = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    current_long = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    experience_years = serializers.IntegerField(required=False)
    kyc_docs_url = serializers.URLField(required=False)

    # ===== VENDOR =====
    business_name = serializers.CharField(required=False)
    gst_number = serializers.CharField(required=False)
    store_address = serializers.CharField(required=False)
    store_lat = serializers.DecimalField(max_digits=10, decimal_places=8, required=False)
    store_long = serializers.DecimalField(max_digits=11, decimal_places=8, required=False)
    opening_hours = serializers.CharField(required=False)
    bank_account_details = serializers.CharField(required=False)


#Added Serializers for Category, Service and Product models#
from .models import Category, Service, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"



from .models import Product, VendorProfile

class ProductSerializer(serializers.ModelSerializer):

    vendor = serializers.PrimaryKeyRelatedField(
        queryset=VendorProfile.objects.all(),
        required=False
    )

    image = serializers.ImageField(required=False)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
            "name",
            "price",
            "stock_quantity",
            "min_stock_alert",
            "image",
            "image_url",
            "description",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


    def update(self, instance, validated_data):

        new_image = validated_data.get("image")

        if new_image and instance.image:
            delete_cloudinary_image(instance.image)

        return super().update(instance, validated_data)

    def create(self, validated_data):
        request = self.context["request"]

        if request.user.role == "VENDOR":
            try:
                vendor = VendorProfile.objects.get(user=request.user)
                validated_data["vendor"] = vendor   # ✅ correct
            except VendorProfile.DoesNotExist:
                raise serializers.ValidationError("Vendor profile not found")

        return Product.objects.create(**validated_data)

# Serviceman
from .models import Serviceman
 
class ServicemanSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")

    class Meta:
        model = Serviceman
        fields = ["id", "name", "category", "latitude", "longitude"]


class VendorNearbySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user_id", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = [
            "id",
            "user_name",
            "phone",
            "business_name",
            "city",
            "state",
            "full_address",
            "store_lat",
            "store_long",
            "profile_image_url",
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


#--------Booking-serializer---------------------
# ================= BOOKING SERIALIZERS =================


    #Booking Serializer
from rest_framework.exceptions import ValidationError
from .models import ServicemanProfile,Booking
from .utils import distance_km
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from datetime import datetime

class BookingCreateSerializer(serializers.ModelSerializer):
    scheduled_time = serializers.CharField()
    services = serializers.PrimaryKeyRelatedField(many=True, queryset=Service.objects.all(), required=False)
    address_id = serializers.IntegerField(required=False)

    class Meta:
        model = Booking
        fields = [
            "serviceman",
            "scheduled_date",
            "scheduled_time",
            "problem_title",
            "problem_description",
            "services",
            "address_id",
        ]

        
    def validate_scheduled_time(self, value):
        try:
            time_obj = datetime.strptime(value, "%I:%M %p").time()
            return time_obj
        except ValueError:
            raise serializers.ValidationError(
                "Time must be in format HH:MM AM/PM (e.g. 10:30 AM)"
            )

    def validate(self, attrs):
        request = self.context["request"]
        serviceman = attrs.get("serviceman")
        address_id = attrs.get("address_id")

        try:
            customer_profile = request.user.customerprofile
        except CustomerProfile.DoesNotExist:
            raise serializers.ValidationError("Customer profile not found")

        # Determine which address to use
        address_text = customer_profile.default_address
        lat = customer_profile.default_lat
        lon = customer_profile.default_long

        # Location checks
        if not lat or not lon:
            raise serializers.ValidationError("Customer location not available. Please provide an address.")

        if not serviceman.current_lat or not serviceman.current_long:
            raise serializers.ValidationError("Serviceman location not available")

        if not serviceman.is_active:
            raise serializers.ValidationError("Serviceman is not active")

        if not serviceman.is_approved:
            raise serializers.ValidationError("Serviceman is not approved")

        dist = distance_km(
            float(lat),
            float(lon),
            float(serviceman.current_lat),
            float(serviceman.current_long),
        )

        if dist > 10:
            raise serializers.ValidationError(
                f"Serviceman is {round(dist,2)} km away. Must be within 10 km."
            )

        # Stash the selected address info for the create() method
        attrs['__booking_address'] = address_text
        attrs['__booking_lat'] = lat
        attrs['__booking_long'] = lon

        return attrs

    def validate_images(self, images):

        if len(images) > 4:
            raise serializers.ValidationError("Maximum 4 images allowed.")

        for image in images:
            if image.size > 5 * 1024 * 1024:   # 5MB
                raise serializers.ValidationError(
                    "Each image must be smaller than 5MB."
                )
        return images
    @staticmethod
    def upload_to_cloudinary(image):
        image.seek(0)

        result = cloudinary.uploader.upload(
            image,
            folder="homefixer/bookings/"
            )
        return result["secure_url"]

    def create(self, validated_data):
        services_data = validated_data.pop("services", [])
        
        # Extract the address fields stashed during validation
        address_id = validated_data.pop("address_id", None)
        booking_address = validated_data.pop("__booking_address", None)
        booking_lat = validated_data.pop("__booking_lat", None)
        booking_long = validated_data.pop("__booking_long", None)
        
        request = self.context["request"]
        customer_profile = request.user.customerprofile
        serviceman = validated_data["serviceman"]

        from .models import PlatformSettings
        settings = PlatformSettings.objects.first()
        platform_fee = settings.platform_fee if settings else Decimal("20.00")

        # 🔥 PRICE CALCULATION
        service_charge = serviceman.visiting_charge
        total_cost = service_charge + platform_fee

        # 🔥 CREATE BOOKING WITH PAYMENT FIRST
        booking = Booking.objects.create(
            customer=customer_profile,
            visiting_charge=serviceman.visiting_charge,
            service_charge=0,
            platform_fee=platform_fee,
            status="PENDING_PAYMENT",
            payment_status="PENDING",
            booking_address=booking_address,
            booking_lat=booking_lat,
            booking_long=booking_long,
            **validated_data
        )   
        
        if services_data:
            booking.services.set(services_data)

        return booking
    
class BookingDetailSerializer(serializers.ModelSerializer):

    serviceman_name = serializers.CharField(
        source="serviceman.user.name",
        read_only=True
    )

    serviceman_skills = serializers.SerializerMethodField()
    
    customer_name = serializers.CharField(
        source="customer.user.name",
        read_only=True
    )

    customer_image = serializers.SerializerMethodField()
    service_charge = serializers.SerializerMethodField()
    platform_fee = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    customer_address = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "status",
            "service_type",
            "scheduled_date",
            "scheduled_time",
            "problem_title",
            "problem_description",
            "image_urls",
            "customer_name",
            "customer_image",
            "serviceman_name",
            "serviceman_skills",
            "customer_address",
            "service_charge",
            "platform_fee",
            "total_amount",
            "created_at",
            "services",
        ]

    def get_serviceman_skills(self, obj):
        if obj.serviceman:
            return obj.serviceman.skills
        return []

    # ✅ FIXED
    def get_service_charge(self, obj):
        return obj.visiting_charge + obj.service_charge
    
    def get_platform_fee(self, obj):
        return obj.platform_fee

    def get_total_amount(self, obj):
        return obj.total_cost
    def get_customer_image(self, obj):

        if obj.customer and obj.customer.profile_image:
            return obj.customer.profile_image.url

        return None
    def get_customer_address(self, obj):
        customer = obj.customer
        
        # Use specific booking address if available, otherwise fallback
        if obj.booking_lat and obj.booking_long:
            return {
                "address": obj.booking_address,
                "lat": obj.booking_lat,
                "long": obj.booking_long,
            }
            
        if not customer:
            return None

        return {
            "address": getattr(customer, "default_address", None),
            "lat": getattr(customer, "default_lat", None),
            "long": getattr(customer, "default_long", None),
        }
    def update_service_type(self):
        if self.service_charge > 0:
            self.service_type = "VISITING_SERVICE"
        else:
            self.service_type = "VISITING"
        
    #Booking tracking response serializer
class BookingTrackingSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    status = serializers.CharField()
    status_text = serializers.CharField()
    serviceman_name = serializers.CharField()
    serviceman_image = serializers.URLField(required=False, allow_null=True)
    serviceman_rating = serializers.FloatField()
    serviceman_lat = serializers.DecimalField(max_digits=10, decimal_places=8)
    serviceman_long = serializers.DecimalField(max_digits=11, decimal_places=8)
    customer_name = serializers.CharField()
    customer_image = serializers.URLField(required=False)
    customer_lat = serializers.DecimalField(max_digits=10, decimal_places=8)
    customer_long = serializers.DecimalField(max_digits=11, decimal_places=8)
    customer_address = serializers.CharField()
    distance_km = serializers.FloatField()
    eta_minutes = serializers.IntegerField()
    image_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False
    )


# ================= SERVICE SERIALIZERS =================

from .models import Service, Category


class ServiceSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "base_price",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Base price must be greater than zero"
            )
        return value

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Service name must be at least 3 characters"
            )
        return value
    

class LocationUpdateSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()    



# ================= PAYMENT SERIALIZERS =================
class PaymentCreateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "amount",
            "status",
            "gateway_order_id",
            "created_at",
        ]
        read_only_fields = fields


# serializers.py

class PaymentVerifySerializer(serializers.Serializer):
    gateway = serializers.ChoiceField(choices=["STRIPE", "RAZORPAY"])

    # Razorpay fields
    razorpay_order_id = serializers.CharField(required=False)
    razorpay_payment_id = serializers.CharField(required=False)
    razorpay_signature = serializers.CharField(required=False)

    # Stripe fields
    payment_intent_id = serializers.CharField(required=False)

class PaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "method",
            "gateway",   # ✅ ADD THIS
            "status",
            "gateway_order_id",
            "gateway_payment_id",
            "created_at",
            "paid_at",
        ]
        
class VerifyStripePaymentSerializer(serializers.Serializer):
    payment_intent_id = serializers.CharField()



class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "service_type",
            "visiting_charge",
            "service_charge",
            "platform_fee",
            "total_cost",
        ]
# serializers.py
from .models import OrderItem

class VendorOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    product_image = serializers.SerializerMethodField()

    def get_product_image(self, obj):
        if obj.product.image:
            return obj.product.image.url
        return None

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_name',
            'product_image',
            'price',        # ✅ use direct field
            'quantity',
            'status'
        ]

from .models import MaterialOrderItem, MaterialOrder

class MaterialOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    product_image = serializers.SerializerMethodField()

    def get_product_image(self, obj):
        if obj.product.image:
            return obj.product.image.url
        return None

    class Meta:
        model = MaterialOrderItem   # ✅ IMPORTANT
        fields = [
            'id',
            'product_name',
            'product_image',
            'price_at_order',
            'quantity'
        ]

class VendorOrderSerializer(serializers.ModelSerializer):
    items = MaterialOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = MaterialOrder
        fields = [
            'id',
            'status',
            'total_cost',
            'created_at',
            'tracking_code',
            'items'   # 🔥 THIS IS KEY
        ]


class BookingItemHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField()
    product_image = serializers.SerializerMethodField()
    item_total = serializers.SerializerMethodField()

    def get_product_image(self, obj):
        try:
            if obj.product and obj.product.image:
                return obj.product.image.url
        except Exception:
            pass
        return getattr(obj, 'product_image', None)

    def get_item_total(self, obj):
        return obj.quantity * obj.product_price

    class Meta:
        model = BookingItem
        fields = [
            "id", "product_name", "product_image", "product_price", 
            "quantity", "item_total", "approval_status"
        ]

class BookingHistorySerializer(serializers.ModelSerializer):
    items = BookingItemHistorySerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_address = serializers.SerializerMethodField()
    customer_lat = serializers.SerializerMethodField()
    customer_long = serializers.SerializerMethodField()
    serviceman_name = serializers.SerializerMethodField()
    product_total = serializers.SerializerMethodField()

    def get_customer_name(self, obj):
        try:
            return obj.customer.user.name if obj.customer and obj.customer.user else None
        except Exception:
            return None

    def get_customer_address(self, obj):
        if obj.booking_address: return obj.booking_address
        return obj.customer.default_address if obj.customer else None

    def get_customer_lat(self, obj):
        if obj.booking_lat: return float(obj.booking_lat)
        return float(obj.customer.default_lat) if obj.customer and obj.customer.default_lat else None

    def get_customer_long(self, obj):
        if obj.booking_long: return float(obj.booking_long)
        return float(obj.customer.default_long) if obj.customer and obj.customer.default_long else None

    def get_serviceman_name(self, obj):
        try:
            return obj.serviceman.user.name if obj.serviceman and obj.serviceman.user else None
        except Exception:
            return None

    def get_product_total(self, obj):
        return sum(
            item.quantity * item.product_price
            for item in obj.items.all()
            if item.approval_status == "APPROVED"
        )

    class Meta:
        model = Booking
        fields = [
            "id", "status", "service_type", "scheduled_date", "scheduled_time",
            "problem_title", "visiting_charge", "service_charge", "platform_fee",
            "product_total", "total_cost", "created_at", "customer_name", "customer_address", "customer_lat", "customer_long", "serviceman_name", "items"
        ]

# ================= 2-STEP PAYMENT SYSTEM SERIALIZERS =================
class PaymentStatusSerializer(serializers.Serializer):
    """
    GET /booking/<id>/payment/status/
    Current payment state overview
    """
    booking_id = serializers.IntegerField(source="id", read_only=True)
    payment_status = serializers.CharField(source="payment_status", read_only=True)
    status = serializers.CharField(read_only=True)
    
    visiting_paid = serializers.SerializerMethodField()
    final_paid = serializers.SerializerMethodField()
    next_payment_type = serializers.SerializerMethodField()
    next_amount = serializers.SerializerMethodField()
    
    payments = serializers.SerializerMethodField()
    
    def get_visiting_paid(self, booking):
        return booking.payments.filter(
            payment_type__in=["VISITING", "VISITING_SERVICE"], 
            status="PAID"
        ).exists()
    
    def get_final_paid(self, booking):
        return booking.payments.filter(
            payment_type="FINAL", 
            status="PAID"
        ).exists()
    
    def get_next_payment_type(self, booking):
        if not self.get_visiting_paid(booking):
            return "VISITING"
        if not self.get_final_paid(booking):
            return "FINAL"
        return None
    
    def get_next_amount(self, booking):
        next_type = self.get_next_payment_type(booking)
        if next_type == "VISITING":
            # Trigger payment creation to calculate amount
            payment = Payment.objects.create(
                booking=booking,
                customer=booking.customer,
                payment_type="VISITING",
                gateway="STRIPE",  # dummy
                status="PENDING"
            )
            amount = payment.amount
            payment.delete()  # cleanup
            return amount
        elif next_type == "FINAL":
            payment = Payment.objects.create(
                booking=booking,
                customer=booking.customer,
                payment_type="FINAL",
                gateway="STRIPE",  # dummy
                status="PENDING"
            )
            amount = payment.amount
            payment.delete()  # cleanup
            return amount
        return None
    
    def get_payments(self, booking):
        return [
            {
                "id": p.id,
                "type": p.payment_type,
                "amount": str(p.amount),
                "status": p.status,
                "created": p.created_at,
                "gateway_order_id": p.gateway_order_id
            }
            for p in booking.payments.all()
        ]


class PaymentCanCreateSerializer(serializers.Serializer):
    """
    POST /booking/<id>/payment/can-create/
    Input: {payment_type: "VISITING|FINAL"}
    """
    payment_type = serializers.ChoiceField(choices=["VISITING", "FINAL"])
    
    # Output fields (read-only)
    can_create = serializers.BooleanField(read_only=True)
    reason = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    
    def validate(self, data):
        booking = self.context["booking"]
        payment_type = data["payment_type"]
        user = self.context["request"].user
        
        from .utils import can_create_payment
        can, reason = can_create_payment(booking, payment_type, user)
        
        # Create temp payment to calculate amount
        temp_payment = Payment.objects.create(
            booking=booking,
            customer=booking.customer,
            payment_type=payment_type,
            gateway="STRIPE",  # dummy
            status="PENDING"
        )
        amount = temp_payment.amount
        temp_payment.delete()
        
        data["can_create"] = can
        data["reason"] = reason
        data["amount"] = amount
        
        return data


# ================= PAYMENT GATEWAY SERIALIZERS =================
class PaymentGatewaySerializer(serializers.Serializer):
    """
    POST /booking/{id}/payment/create/
    Customer selects payment method
    """
    payment_type = serializers.ChoiceField(choices=["VISITING", "FINAL"])
    gateway = serializers.ChoiceField(choices=["STRIPE", "RAZORPAY"])
    
    # Read-only (auto-calculated)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.CharField(default="INR", read_only=True)
    
    def validate(self, data):
        booking_id = self.context["booking_id"]
        payment_type = data["payment_type"]
        gateway = data["gateway"]
        
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        
        # Create temp payment to validate amount
        temp_payment = Payment.objects.create(
            booking=booking,
            customer=booking.customer,
            payment_type=payment_type,
            gateway=gateway,
            status="PENDING"
        )
        
        data["amount"] = temp_payment.amount
        data["currency"] = "INR"
        temp_payment.delete()
        
        return data


class StripePaymentResponseSerializer(serializers.Serializer):
    """
    Stripe payment response
    """
    client_secret = serializers.CharField()
    payment_intent_id = serializers.CharField()
    

class RazorpayPaymentResponseSerializer(serializers.Serializer):
    """
    Razorpay payment response  
    """
    order_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    key_id = serializers.CharField()

from .models import Wallet, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'booking', 'type', 'amount', 'description', 'created_at']

class WalletSerializer(serializers.ModelSerializer):
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'updated_at', 'transactions']

    def get_transactions(self, obj):
        transactions = Transaction.objects.filter(wallet=obj).order_by('-created_at')[:20]
        return TransactionSerializer(transactions, many=True).data


from .models import PlatformSettings

class PlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSettings
        fields = ['id', 'platform_fee']

from .models import WithdrawalRequest

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    payment_method = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user', 'user_email', 'user_name', 'user_role',
            'amount', 'status', 'payment_method', 'upi_id', 'admin_payment_method', 'transaction_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'user_name', 'user_role', 'status', 'transaction_id', 'admin_payment_method', 'created_at', 'updated_at']


# =================== SLIM PROFILE CREATE SERIALIZERS ===================
# POST /user/customer-profile/, /user/serviceman-profile/, /user/vendor-profile/
# Intentionally exclude: name, email, phone, password

class CustomerProfileCreateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            'default_address',
            'default_lat',
            'default_long',
            'profile_image',
            'profile_image_url',
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


class ServicemanProfileCreateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)
    kyc_document = serializers.ImageField(required=False, write_only=True)
    kyc_document_url = serializers.SerializerMethodField(read_only=True)
    skills = serializers.CharField(required=False, help_text='Comma-separated skills e.g. Plumber,Electrician')

    class Meta:
        model = ServicemanProfile
        fields = [
            'is_online',
            'current_lat',
            'current_long',
            'experience_years',
            'skills',
            'upi_id',
            'profile_image',
            'profile_image_url',
            'kyc_document',
            'kyc_document_url',
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def get_kyc_document_url(self, obj):
        if obj.kyc_document:
            return obj.kyc_document.url
        return None

    def validate_skills(self, value):
        if value:
            return [skill.strip() for skill in value.split(',')]
        return []


class VendorProfileCreateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, write_only=True)
    profile_image_url = serializers.SerializerMethodField(read_only=True)
    gst_certificate = serializers.FileField(required=False, write_only=True)
    store_registration = serializers.FileField(required=False, write_only=True)
    id_proof = serializers.FileField(required=False, write_only=True)
    gst_certificate_url = serializers.SerializerMethodField(read_only=True)
    store_registration_url = serializers.SerializerMethodField(read_only=True)
    id_proof_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'business_name',
            'gst_number',
            'contact_number',
            'business_email',
            'opening_time',
            'closing_time',
            'city',
            'state',
            'full_address',
            'store_lat',
            'store_long',
            'account_holder_name',
            'bank_name',
            'account_number',
            'ifsc_code',
            'upi_id',
            'profile_image',
            'profile_image_url',
            'gst_certificate',
            'gst_certificate_url',
            'store_registration',
            'store_registration_url',
            'id_proof',
            'id_proof_url',
        ]

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def get_gst_certificate_url(self, obj):
        if obj.gst_certificate:
            return obj.gst_certificate.url
        return None

    def get_store_registration_url(self, obj):
        if obj.store_registration:
            return obj.store_registration.url
        return None

    def get_id_proof_url(self, obj):
        if obj.id_proof:
            return obj.id_proof.url
        return None

class AdminServicemanBookingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user_id', read_only=True)
    bookings = serializers.SerializerMethodField()
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ServicemanProfile
        fields = ['id', 'name', 'email', 'bookings']

    def get_bookings(self, obj):
        # Use prefetched bookings if available to avoid N+1 queries
        bookings = getattr(obj, 'prefetched_bookings', obj.booking_set.all().order_by('-created_at'))
        return BookingHistorySerializer(bookings, many=True).data

class ServicemanVendorOrderDetailSerializer(serializers.ModelSerializer):
    vendor_details = VendorProfileSerializer(source='vendor', read_only=True)
    items = MaterialOrderItemSerializer(many=True, read_only=True)
    service_charge = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(source='total_cost', read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = MaterialOrder
        fields = [
            'id', 'status', 'created_at', 'tracking_code', 
            'vendor_details', 'items', 'service_charge', 'total_amount'
        ]

    def get_service_charge(self, obj):
        return obj.booking.service_charge if obj.booking else 0


