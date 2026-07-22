from django.urls import path
from . import views
from .views import (
    BookingDetailAPIView,
    BookingTrackingAPI,
    AdminVendorControlAPI,
    CategoryNearbyServicemanAPI,
    CreatePaymentAPIView,
    CreateRazorpayPaymentAPIView,
    CustomerBookingHistoryAPI,
    CustomerCancelBookingAPI,
    LoginSendOTPAPI,
    LoginVerifyOTPAPI,
    MarkVendorCollectedAPI,
    NearbyVendorAPI,
    PaymentStatusAPIView,
    ProductDeleteAPI,
    ProductListAPI,
    RegisterSendOTPAPI,
    RegisterVerifyOTPAPI,
    RegisterCompleteAPI,
    ServicemanBookingActionAPI,
    ServicemanCompleteBookingAPI,
    ServicemanBookingHistoryAPI,
    ServicemanLocationUpdateAPI,
    ServicemanProfileUpdateAPI,
    UpdateProductAndServiceChargeAPI,
    UserProfileAPI,
    LogoutAPI,
    VendorAcceptOrderAPI,
    VendorDeliverOrderAPI,
    VendorProfileUpdateAPI,
    CustomerProfileUpdateAPI,
    ProfileAPI,
    SaveProfileAPI,
    EmailPasswordLoginAPI,
    NearbyServicemanAPI,
    PendingVendorsAPI,
    PendingServicemenAPI,
    AdminServicemanControlAPI,
    ProductCreateAPI,
    ProductUpdateAPI,
    VendorTrackingAPI,
  
    AddProductAndServiceAPI,
    ApproveBookingItemsAPI,
    VendorOrdersView,
    VerifyPaymentAPIView,
    VerifyRazorpayPaymentAPIView,
    VerifyStripePaymentAPIView,
    WalletPayForBookingAPI,
    GoogleLoginAPI,
    CustomerProfileAPI,
    ServicemanProfileAPI,
    VendorProfileAPI,
    ServicemanVendorOrderAPI,
    VendorProductListAPI,
    RegisterFCMDeviceAPI,
)

from .admin_views import (
    AdminUserManagementAPI,
    AdminUserDetailAPI,
    CategoryListAPI,
    CategoryCreateAPI,
    CategoryDetailAPI,
    AdminPlatformSettingsAPI,
    AdminAllBookingsAPI,
    AdminServicemanBookingAPI,
    AdminCategoryListAPI,
)

urlpatterns = [

    # ================= AUTH =================
    path("login/", EmailPasswordLoginAPI.as_view(), name="login"),
    path("google-login/", GoogleLoginAPI.as_view(), name="google-login-direct"),
    path("logout/", LogoutAPI.as_view(), name="logout-direct"),
    path("auth/google-login/", GoogleLoginAPI.as_view(), name="google-login"),
    path("auth/logout/", LogoutAPI.as_view(), name="logout"),

    path("auth/login/send-otp/", LoginSendOTPAPI.as_view()),
    path("auth/login/verify-otp/", LoginVerifyOTPAPI.as_view()),

    path("auth/register/send-otp/", RegisterSendOTPAPI.as_view()),
    path("auth/register/verify-otp/", RegisterVerifyOTPAPI.as_view()),
    path("auth/register/complete/", RegisterCompleteAPI.as_view()),


    # ================= USER =================
    path("user/profile/", UserProfileAPI.as_view()),
    path("user/customer-profile/", CustomerProfileAPI.as_view(), name="user_customer-profile_create"),
    path("user/serviceman-profile/", ServicemanProfileAPI.as_view(), name="user_serviceman-profile_create"),
    path("user/vendor-profile/", VendorProfileAPI.as_view(), name="user_vendor-profile_create"),



    path("profile/", ProfileAPI.as_view()),
    path("profile/save/", SaveProfileAPI.as_view()),
    path("profile/customer/update/", CustomerProfileUpdateAPI.as_view()),
    path("profile/serviceman/update/", ServicemanProfileUpdateAPI.as_view()),
    path("profile/vendor/update/", VendorProfileUpdateAPI.as_view()),

    # ================= CUSTOMER ADDRESSES =================
    path("customer/addresses/", views.CustomerAddressListCreateAPI.as_view(), name="customer-addresses"),
    path("customer/addresses/<int:pk>/", views.CustomerAddressDetailAPI.as_view(), name="customer-address-detail"),


    # ================= NEARBY =================
    path("servicemen/nearby/", NearbyServicemanAPI.as_view()),
    path("servicemen/category-nearby/", CategoryNearbyServicemanAPI.as_view()),
    path("vendors/nearby/", NearbyVendorAPI.as_view(), name="vendors-nearby"),


    # ================= ADMIN =================
    path("admin/users/", AdminUserManagementAPI.as_view()),
    path("admin/users/<int:pk>/", AdminUserDetailAPI.as_view()),

    path("admin/servicemen/pending/", PendingServicemenAPI.as_view()),
    path("admin/vendors/pending/", PendingVendorsAPI.as_view()),

    path("admin/servicemen/<int:pk>/control/", AdminServicemanControlAPI.as_view()),
    path("admin/vendors/<int:pk>/control/", AdminVendorControlAPI.as_view()),

    path("admin/customers/", views.AdminCustomerListAPI.as_view()),
    path("admin/servicemen/all/", views.AdminServicemanListAPI.as_view()),
    path("admin/vendors/all/", views.AdminVendorListAPI.as_view()),
    
    path("admin/settings/platform-fee/", AdminPlatformSettingsAPI.as_view()),
    path("admin/bookings/all/", AdminAllBookingsAPI.as_view()),

    # 🔥 NEW PAYMENT ENDPOINTS
    path("booking/<int:booking_id>/payment/create/", views.PaymentCreateAPIView.as_view()),
    path('payment/<int:payment_id>/verify/stripe/', VerifyStripePaymentAPIView.as_view()),
    path('payment/<int:payment_id>/verify/razorpay/', VerifyRazorpayPaymentAPIView.as_view()),
    path('booking/<int:booking_id>/payment/razorpay/create/', CreateRazorpayPaymentAPIView.as_view()),
    path('payment/<int:payment_id>/status/', PaymentStatusAPIView.as_view()),
 

    # ================= CATEGORY =================
    path("categories/", CategoryListAPI.as_view()),

    path("admin/categories/create/", CategoryCreateAPI.as_view()),
    path("admin/categories/all/", AdminCategoryListAPI.as_view()),
    path("admin/categories/<int:pk>/", CategoryDetailAPI.as_view()),


    # ================= PRODUCTS =================
    path("products/", ProductListAPI.as_view()),
    path("products/create/", ProductCreateAPI.as_view()),
    path("products/<int:pk>/update/", ProductUpdateAPI.as_view()),
    path("products/<int:pk>/delete/", ProductDeleteAPI.as_view()),

    path("products/nearby/", views.NearbyProductAPI.as_view()),
    path("product-categories/", views.ProductCategoryAPI.as_view()),
    path("product-categories/<int:pk>/delete/", views.ProductCategoryDeleteAPI.as_view()),


    # ================= BOOKING =================
    path("booking/create/", views.BookingCreateAPIView.as_view()),

    path("booking/<int:booking_id>/cancel/", CustomerCancelBookingAPI.as_view()),
    path("booking/<int:booking_id>/details/", BookingDetailAPIView.as_view()),
    path("booking/<int:booking_id>/summary/", views.BookingSummaryAPI.as_view()),
    path("bookings/history/", CustomerBookingHistoryAPI.as_view()),

    path("booking/<int:booking_id>/action/", ServicemanBookingActionAPI.as_view()),
    path("bookings/<int:booking_id>/track/", BookingTrackingAPI.as_view()),

    path("serviceman/bookings/", views.ServicemanBookingRequestsAPI.as_view()),
    path("serviceman/bookings/history/", ServicemanBookingHistoryAPI.as_view()),
    path("serviceman/booking/<int:booking_id>/complete/", ServicemanCompleteBookingAPI.as_view()),



    # ================= BOOKING PRODUCT FLOW =================
    path("booking/<int:booking_id>/add-product/", AddProductAndServiceAPI.as_view()),
    path("booking/<int:booking_id>/update-product-service/", UpdateProductAndServiceChargeAPI.as_view()),
    path("booking/<int:booking_id>/approve/", ApproveBookingItemsAPI.as_view()),


   

    # ================= VENDOR =================
    path("vendor/orders/", VendorOrdersView.as_view()),
    path("vendor/order/<int:order_id>/accept/", VendorAcceptOrderAPI.as_view()),
    path("vendor/order/<int:order_id>/deliver/", VendorDeliverOrderAPI.as_view()),
    path("vendor/order/<int:order_id>/collect/", MarkVendorCollectedAPI.as_view()),

    path("booking/<int:booking_id>/vendor-tracking/", VendorTrackingAPI.as_view()),
    path("vendor/my-products/", VendorProductListAPI.as_view()),


    path("serviceman/location/update/", ServicemanLocationUpdateAPI.as_view()),

    # ================= WALLET =================
    path("wallet/", views.UserWalletAPI.as_view()),
    path("wallet/booking/<int:booking_id>/pay/", WalletPayForBookingAPI.as_view(), name="wallet-pay-booking"),
    path("wallet/withdrawal/request/", views.WithdrawalRequestAPI.as_view(), name="withdrawal-request"),
    path("admin/withdrawals/", views.AdminWithdrawalListAPI.as_view(), name="admin-withdrawals"),
    path("admin/withdrawals/<int:pk>/", views.AdminWithdrawalActionAPI.as_view(), name="admin-withdrawal-action"),
    path("admin/servicemen/bookings/", AdminServicemanBookingAPI.as_view(), name="admin-serviceman-bookings"),
    path("serviceman/vendor-orders/", ServicemanVendorOrderAPI.as_view(), name="serviceman-vendor-orders"),
    path("register-device/", RegisterFCMDeviceAPI.as_view(), name="register-device"),
]