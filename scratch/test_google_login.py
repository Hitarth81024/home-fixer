import os
import sys
import django

# Set up django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home_fixer.settings")
django.setup()

from home.models import User, CustomerProfile, ServicemanProfile
from rest_framework_simplejwt.tokens import RefreshToken

print("--- Google Auth Backend Mock Test ---")

email = "mock.user@gmail.com"
role = "customer"
google_id = "1234567890123456789"
name = "Mock User"
picture = "https://lh3.googleusercontent.com/a/mock-pic"

# 1. Clean up first if test user exists
User.objects.filter(email=email).delete()
print("Cleaned up existing mock user if any.")

# 2. Map role
role_map = {
    'customer': 'CUSTOMER',
    'service-man': 'SERVICEMAN',
}
db_role = role_map.get(role, 'CUSTOMER')

# 3. Create user
print(f"Creating mock user with email: {email}, role: {db_role}...")
user = User.objects.create_user(
    email=email,
    role=db_role
)
user.name = name
user.full_name = name
user.google_id = google_id
user.profile_picture = picture
user.is_verified = True
user.save()

print("User created successfully.")
print(f"User Info: ID={user.id}, Name={user.name}, FullName={user.full_name}, Phone={user.phone}, Role={user.role}, GoogleID={user.google_id}, Picture={user.profile_picture}")

# 4. Verify profiles
if user.role == "CUSTOMER":
    profile, created = CustomerProfile.objects.get_or_create(user=user)
    print(f"Customer profile verified. Created={created}")
elif user.role == "SERVICEMAN":
    profile, created = ServicemanProfile.objects.get_or_create(user=user)
    print(f"Serviceman profile verified. Created={created}")

# 5. Generate SimpleJWT tokens
print("Generating JWT tokens...")
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)
refresh_token = str(refresh)
print(f"Access Token: {access_token[:30]}...")
print(f"Refresh Token: {refresh_token[:30]}...")

# 6. Clean up
User.objects.filter(email=email).delete()
print("Test complete. Cleaned up mock user.")
print("SUCCESS!")
