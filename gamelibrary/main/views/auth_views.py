from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from ..models import Users
from ..forms import LoginForm, RegistrationForm
import pyotp
import qrcode
from io import BytesIO
import base64

# Helper: generate QR code for TOTP app
def generate_totp_qr(user):
    if not user.totp_secret:  # Only generate if it doesn't exist
        user.totp_secret = pyotp.random_base32()
        user.save()
    totp_uri = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
        name=user.username,
        issuer_name="Game Library"
    )
    img = qrcode.make(totp_uri)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return qr_code_base64


# LOGIN VIEW
def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = Users.objects.get(username=username)
                if check_password(password, user.password):
                    request.session["pending_user_id"] = user.id

                    # Admin users skip TOTP
                    if user.role == "admin":
                        request.session["user_id"] = user.id
                        return redirect("library")

                    return redirect("verify_totp")
                else:
                    messages.error(request, "Invalid password")
            except Users.DoesNotExist:
                messages.error(request, "User does not exist")
    return render(request, 'login.html', {'form': form})


# VERIFY TOTP VIEW
def verify_totp(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return redirect("login")

    user = Users.objects.get(id=user_id)

    # Make sure secret exists, but NEVER regenerate it
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save()

    totp = pyotp.TOTP(user.totp_secret)

    if request.method == "POST":
        code = request.POST.get("otp")
        if totp.verify(code, valid_window=1):
            user.totp_verified = True
            user.save()
            request.session["user_id"] = user.id
            del request.session["pending_user_id"]
            return redirect("library")
        else:
            messages.error(request, "Invalid code. Make sure your device time is correct.")

    # Generate QR code (REAL FIXED VERSION)
    qr_code_base64 = None
    if not user.totp_verified:
        totp_uri = totp.provisioning_uri(
            name=user.username,
            issuer_name="Game Library"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=4
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, "verify_totp.html", {
        "qr_code_base64": qr_code_base64
    })


# LOGOUT
def logout_view(request):
    request.session.flush()
    return redirect('login')


# REGISTER VIEW
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.totp_secret = pyotp.random_base32()  # generate secret at registration
            user.save()
            messages.success(request, "Account created successfully. Scan QR code in your authenticator app after login.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})
