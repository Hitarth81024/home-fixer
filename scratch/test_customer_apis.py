import os
import sys
import time
import django
from decimal import Decimal

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home_fixer.settings")
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from home.models import CustomerProfile, Category, ServicemanProfile

User = get_user_model()

def run_tests():
    client = APIClient()
    
    # 0. Create test serviceman
    sm_email = "test_serviceman_speed@example.com"
    sm_phone = "9876543288"
    User.objects.filter(email=sm_email).delete()
    User.objects.filter(phone=sm_phone).delete()
    sm_user = User.objects.create(
        email=sm_email,
        phone=sm_phone,
        role="SERVICEMAN",
        name="Test Serviceman",
        is_verified=True
    )
    sm_profile = ServicemanProfile.objects.create(
        user=sm_user,
        is_online=True,
        is_approved=True,
        is_active=True,
        is_available=True,
        current_lat=Decimal("40.71280000"),
        current_long=Decimal("-74.00600000"),
        experience_years=5,
        visiting_charge=Decimal("100.00"),
        skills=["Plumbing"]
    )
    print(f"Created test serviceman: {sm_email}")

    # 1. Create/Get test customer user
    email = "test_customer_speed@example.com"
    phone = "9876543299"
    # Delete if exists to avoid unique constraint issues
    User.objects.filter(email=email).delete()
    User.objects.filter(phone=phone).delete()
    
    user = User.objects.create(
        email=email,
        phone=phone,
        role="CUSTOMER",
        name="Test Customer",
        is_verified=True
    )
    user.set_password("password123")
    user.save()
    print(f"Created fresh test customer user: {email}")
        
    # Get or create CustomerProfile
    profile, p_created = CustomerProfile.objects.get_or_create(
        user=user,
        defaults={
            "default_address": "123 Main St, New York, NY",
            "default_lat": Decimal("40.71280000"),
            "default_long": Decimal("-74.00600000")
        }
    )
    if p_created:
        print("Created CustomerProfile.")
        
    # Ensure there is at least one Category for category search test
    Category.objects.get_or_create(
        name="Plumbing",
        defaults={"category_type": "SERVICE", "visiting_charge": Decimal("150.00")}
    )

    # Force authenticate
    client.force_authenticate(user=user)
    
    endpoints = [
        ("Booking (Create)", "/api/booking/create/", "POST", {
            "serviceman": sm_user.id,
            "scheduled_date": "2026-06-01",
            "scheduled_time": "10:30 AM",
            "problem_title": "Test Booking"
        }, "multipart"),
        ("Customer Addresses (List)", "/api/customer/addresses/", "GET", None, "json"),
        ("Customer Addresses (Create)", "/api/customer/addresses/", "POST", {
            "address": "456 Broadway, New York, NY",
            "latitude": "40.72000000",
            "longitude": "-74.01000000"
        }, "json"),
        ("Customer Profile (Detail)", "/api/user/profile/", "GET", None, "json"),
        ("Customer Profile (Create/Save)", "/api/user/customer-profile/", "POST", {
            "default_address": "789 Third Ave, New York, NY",
            "default_lat": "40.73000000",
            "default_long": "-74.02000000"
        }, "multipart"),
        ("Customer Booking History", "/api/bookings/history/", "GET", None, "json"),
        ("User Wallet Details", "/api/wallet/", "GET", None, "json"),
        ("Category List", "/api/categories/", "GET", None, "json"),
        ("Product List", "/api/products/", "GET", None, "json"),
        ("Nearby Servicemen (with coordinates)", "/api/servicemen/nearby/?lat=40.7128&lon=-74.0060", "GET", None, "json"),
        ("Servicemen Category Nearby", "/api/servicemen/category-nearby/?lat=40.7128&lon=-74.0060&category=Plumbing", "GET", None, "json"),
    ]

    print("\n" + "="*80)
    print(f"{'Endpoint Description':<35} | {'Method':<6} | {'Status':<6} | {'Speed (ms)':<10} | {'Status Details'}")
    print("="*80)

    for desc, url, method, data, fmt in endpoints:
        start_time = time.perf_counter()
        
        try:
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, data=data, format=fmt)
            else:
                continue
            
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            
            status_text = "OK" if response.status_code in [200, 201] else "FAIL"
            print(f"{desc:<35} | {method:<6} | {status_text:<6} | {elapsed_ms:>8.2f} | HTTP {response.status_code}")
            
            # Print response preview on error
            if response.status_code not in [200, 201]:
                if hasattr(response, 'data'):
                    print(f"   -> Error Response: {response.data}")
                else:
                    print(f"   -> Error Response content: {response.content[:200]}")
                
        except Exception as e:
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            print(f"{desc:<35} | {method:<6} | EXCEPT | {elapsed_ms:>8.2f} | Exception: {str(e)}")

    print("="*80 + "\n")

    # Clean up test user & profile
    # Keep them so subsequent runs are faster or delete them
    # User.objects.filter(email=email).delete()

if __name__ == "__main__":
    run_tests()
