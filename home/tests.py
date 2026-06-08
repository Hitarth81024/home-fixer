from django.test import TestCase
from rest_framework.test import APITestCase
from django.utils import timezone
from decimal import Decimal
from home.models import User, CustomerProfile, ServicemanProfile, Booking, Wallet, Transaction

class ServiceCompletionPaymentTests(APITestCase):

    def setUp(self):
        # Create customer user and profile
        self.customer_user = User.objects.create_user(
            email="customer@example.com",
            password="password123",
            phone="1234567891",
            role="CUSTOMER"
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.customer_user)

        # Create serviceman user and profile
        self.serviceman_user = User.objects.create_user(
            email="serviceman@example.com",
            password="password123",
            phone="1234567892",
            role="SERVICEMAN"
        )
        self.serviceman_profile = ServicemanProfile.objects.create(
            user=self.serviceman_user,
            is_approved=True,
            is_available=True,
            visiting_charge=Decimal("150.00")
        )

    def test_complete_visiting_booking_blocked_when_pending(self):
        """
        Serviceman cannot complete a VISITING booking if the customer has not paid the visiting charge (status is PENDING).
        """
        booking = Booking.objects.create(
            customer=self.customer_profile,
            serviceman=self.serviceman_profile,
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time(),
            problem_title="Need repair",
            service_type="VISITING",
            visiting_charge=Decimal("150.00"),
            platform_fee=Decimal("20.00"),
            payment_status="PENDING",
            status="PENDING_PAYMENT"
        )

        self.client.force_authenticate(user=self.serviceman_user)
        response = self.client.post(f"/api/serviceman/booking/{booking.id}/complete/")
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Visiting payment is not completed yet", response.data["error"])

        # Verify booking status remains unchanged
        booking.refresh_from_db()
        self.assertEqual(booking.status, "PENDING_PAYMENT")
        self.assertEqual(booking.payment_status, "PENDING")

    def test_complete_visiting_booking_allowed_when_partial(self):
        """
        Serviceman can complete a VISITING booking if the customer has paid the visiting charge (status becomes PARTIAL).
        """
        booking = Booking.objects.create(
            customer=self.customer_profile,
            serviceman=self.serviceman_profile,
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time(),
            problem_title="Need repair",
            service_type="VISITING",
            visiting_charge=Decimal("150.00"),
            platform_fee=Decimal("20.00"),
            payment_status="PARTIAL",
            status="PENDING"
        )

        self.client.force_authenticate(user=self.serviceman_user)
        response = self.client.post(f"/api/serviceman/booking/{booking.id}/complete/")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Booking completed successfully", response.data["message"])

        # Verify booking status becomes completed and paid
        booking.refresh_from_db()
        self.assertEqual(booking.status, "COMPLETED")
        self.assertEqual(booking.payment_status, "PAID")

    def test_complete_visiting_service_booking_blocked_when_partial(self):
        """
        Serviceman cannot complete a VISITING_SERVICE booking if the customer has not paid the final charge (status is PARTIAL).
        """
        booking = Booking.objects.create(
            customer=self.customer_profile,
            serviceman=self.serviceman_profile,
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time(),
            problem_title="Need repair",
            service_type="VISITING_SERVICE",
            visiting_charge=Decimal("150.00"),
            service_charge=Decimal("200.00"),
            platform_fee=Decimal("20.00"),
            payment_status="PARTIAL",
            status="ONGOING"
        )

        self.client.force_authenticate(user=self.serviceman_user)
        response = self.client.post(f"/api/serviceman/booking/{booking.id}/complete/")
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Final payment is not completed yet", response.data["error"])

        # Verify booking status remains unchanged
        booking.refresh_from_db()
        self.assertEqual(booking.status, "ONGOING")
        self.assertEqual(booking.payment_status, "PARTIAL")

    def test_complete_visiting_service_booking_allowed_when_paid(self):
        """
        Serviceman can call complete API if payment status is already PAID (e.g. customer completed payment).
        """
        booking = Booking.objects.create(
            customer=self.customer_profile,
            serviceman=self.serviceman_profile,
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time(),
            problem_title="Need repair",
            service_type="VISITING_SERVICE",
            visiting_charge=Decimal("150.00"),
            service_charge=Decimal("200.00"),
            platform_fee=Decimal("20.00"),
            payment_status="PAID",
            status="COMPLETED"
        )

        self.client.force_authenticate(user=self.serviceman_user)
        response = self.client.post(f"/api/serviceman/booking/{booking.id}/complete/")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("Booking completed successfully", response.data["message"])

    def test_wallet_pay_final_calls_mark_as_completed(self):
        """
        Wallet payment for FINAL charge correctly completes the booking, marks the serviceman as available, and credits the wallet.
        """
        booking = Booking.objects.create(
            customer=self.customer_profile,
            serviceman=self.serviceman_profile,
            scheduled_date=timezone.now().date(),
            scheduled_time=timezone.now().time(),
            problem_title="Need repair",
            service_type="VISITING_SERVICE",
            visiting_charge=Decimal("150.00"),
            service_charge=Decimal("200.00"),
            platform_fee=Decimal("20.00"),
            payment_status="PARTIAL",
            status="ONGOING"
        )

        # Fund customer wallet
        customer_wallet, _ = Wallet.objects.get_or_create(user=self.customer_user)
        customer_wallet.balance = Decimal("500.00")
        customer_wallet.save()

        # Mark serviceman unavailable since they are working
        self.serviceman_profile.is_available = False
        self.serviceman_profile.save()

        # Call the wallet pay API for FINAL payment
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            f"/api/wallet/booking/{booking.id}/pay/",
            data={"payment_type": "FINAL", "gateway": "RAZORPAY"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "FULLY_PAID_BY_WALLET")

        # Verify booking status is COMPLETED and PAID
        booking.refresh_from_db()
        self.assertEqual(booking.status, "COMPLETED")
        self.assertEqual(booking.payment_status, "PAID")

        # Verify serviceman is marked available
        self.serviceman_profile.refresh_from_db()
        self.assertTrue(self.serviceman_profile.is_available)

        # Verify serviceman wallet is credited with service_charge + visiting_charge
        serviceman_wallet, _ = Wallet.objects.get_or_create(user=self.serviceman_user)
        self.assertEqual(serviceman_wallet.balance, Decimal("350.00")) # 200 + 150
