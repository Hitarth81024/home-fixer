import threading
import time
from .models import Booking, ServicemanProfile, Wallet, Transaction
from .utils import distance_km
from django.db import transaction

from django.db import close_old_connections

def refund_booking(booking):
    paid_payments = booking.payments.filter(status="PAID")
    total_refund = sum(payment.amount for payment in paid_payments)
    
    if total_refund > 0:
        customer_user = booking.customer.user
        wallet, _ = Wallet.objects.get_or_create(user=customer_user)
        wallet.balance += total_refund
        wallet.save(update_fields=["balance"])
        
        Transaction.objects.create(
            wallet=wallet,
            booking=booking,
            type="CREDIT",
            amount=total_refund,
            description="Refund due to unavailable serviceman"
        )

def final_cancel_check(booking_id):
    time.sleep(60) # Wait remaining 60s (total 120s / 2 min)
    close_old_connections()
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        close_old_connections()
        return
        
    if booking.status == 'PENDING':
        # No one accepted in 270s
        with transaction.atomic():
            booking.status = 'CANCELLED'
            # Note: "due to heavy booking service man is not available"
            # We can put this in problem_description or a new message field.
            # But the user said "say due to heavy booking...", typically handled via a notification.
            # We'll append it to description for now or just cancel.
            booking.problem_title = "CANCELLED: Due to heavy booking service man is not available"
            booking.save(update_fields=['status', 'problem_title'])
            
            # Refund
            refund_booking(booking)

            from .fcm import notify_user
            notify_user(
                booking.customer,
                "Booking Auto-Cancelled",
                f"Booking #{booking.id} was cancelled due to no available servicemen. You have been fully refunded.",
                {"booking_id": str(booking.id), "type": "booking_auto_cancelled"}
            )
    close_old_connections()

def reassign_check(booking_id):
    time.sleep(60) # Wait 60s
    close_old_connections()
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        close_old_connections()
        return
        
    if booking.status == 'PENDING':
        with transaction.atomic():
            current_serviceman = booking.serviceman
            customer_lat = float(booking.booking_lat) if booking.booking_lat else (float(booking.customer.default_lat) if booking.customer.default_lat else 0)
            customer_lon = float(booking.booking_long) if booking.booking_long else (float(booking.customer.default_long) if booking.customer.default_long else 0)
            
            # Find nearby available servicemen
            available_servicemen = ServicemanProfile.objects.filter(
                is_active=True,
                is_approved=True,
                is_available=True
            )
            if current_serviceman:
                available_servicemen = available_servicemen.exclude(user=current_serviceman.user)
                
            nearby_servicemen = []
            for sm in available_servicemen:
                if sm.current_lat and sm.current_long:
                    dist = distance_km(customer_lat, customer_lon, float(sm.current_lat), float(sm.current_long))
                    if dist <= 10:
                        nearby_servicemen.append(sm)
            
            if nearby_servicemen:
                # Assign to the first nearby one
                booking.serviceman = nearby_servicemen[0]
                booking.save(update_fields=['serviceman'])

                from .fcm import notify_user
                if booking.serviceman and booking.serviceman.user:
                    notify_user(
                        booking.serviceman.user,
                        "Booking Reassigned",
                        f"Booking #{booking.id} has been reassigned to you",
                        {"booking_id": str(booking.id), "type": "booking_reassigned"}
                    )

            # Start the 180s timer for final check (270s total)
            threading.Thread(target=final_cancel_check, args=(booking_id,), daemon=True).start()
    close_old_connections()

def start_booking_assignment_flow(booking_id):
    # This will be called when the booking becomes PENDING
    threading.Thread(target=reassign_check, args=(booking_id,), daemon=True).start()
