import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyResetTokenResponse,
)
from app.schemas.profile import (
    BeneficiaryProfileInput,
    CitizenProfileResponse,
    calculate_profile_completion,
)
from app.services.email_service import EmailService
from app.services.google_auth_service import verify_google_id_token

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
def register(
    req: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registers a new user (default role: BENEFICIARY).
    Hashes password securely with bcrypt and checks for duplicate identifiers.
    """
    # Check for duplicate email
    if req.email:
        existing_email = db.query(User).filter(User.email == str(req.email)).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )

    # Check for duplicate phone
    if req.phone:
        existing_phone = db.query(User).filter(User.phone == req.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this phone number already exists."
            )

    # Public registration always forces default BENEFICIARY role for security
    role_val = UserRole.BENEFICIARY.value

    # Create user
    user = User(
        email=str(req.email) if req.email else None,
        phone=req.phone,
        hashed_password=hash_password(req.password),
        role=role_val,
        preferred_language=req.preferred_language or "en",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT access token"
)
def login(
    req: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticates user via email or phone + password.
    Returns a signed JWT access token upon successful authentication.
    """
    identifier = req.identifier.strip()

    # Search user by email or phone
    user = db.query(User).filter(
        (User.email == identifier) | (User.phone == identifier)
    ).first()

    # Generic invalid credentials message to prevent account enumeration
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid identifier or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Issue access token
    access_token = create_access_token(
        user_id=user.user_id,
        role=user.role,
        email=user.email,
        phone=user.phone
    )

    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Authenticate or register user with verified Google ID token"
)
def google_login(
    req: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticates a user via verified Google OAuth ID token.
    - Cryptographically validates Google ID token.
    - If user exists by google_id, authenticates immediately.
    - If user exists by email, safely associates google_id (account linking).
    - If user does not exist, registers new BENEFICIARY user with verified Google profile.
    - Returns signed JWT access token.
    """
    google_info = verify_google_id_token(req.id_token)

    # 1. Search by google_id
    user = db.query(User).filter(User.google_id == google_info.google_id).first()

    # 2. Search by verified email for safe Account Linking
    if not user and google_info.email:
        user = db.query(User).filter(User.email == google_info.email).first()
        if user:
            # Associate Google account without overwriting existing password or roles
            user.google_id = google_info.google_id
            if not user.full_name and google_info.full_name:
                user.full_name = google_info.full_name
            if not user.avatar_url and google_info.avatar_url:
                user.avatar_url = google_info.avatar_url
            db.commit()
            db.refresh(user)

    # 3. Create new user if account doesn't exist
    if not user:
        import secrets
        user = User(
            email=google_info.email,
            full_name=google_info.full_name,
            avatar_url=google_info.avatar_url,
            auth_provider="GOOGLE",
            google_id=google_info.google_id,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role=UserRole.BENEFICIARY.value,
            preferred_language=req.preferred_language or "en",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Issue access token
    access_token = create_access_token(
        user_id=user.user_id,
        role=user.role,
        email=user.email,
        phone=user.phone
    )

    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user identity"
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Returns current authenticated user details from the JWT bearer token.
    """
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user session"
)
def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logs out the current user session.
    """
    return MessageResponse(message="Successfully logged out.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset link"
)
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Sends password reset instructions to the provided email if an account exists.
    Strictly protects against account enumeration by always returning the same response.
    Applies rate limiting to prevent repeated rapid requests.
    """
    clean_email = str(req.email).strip().lower()
    generic_response = MessageResponse(
        message="If an account exists for this email, you'll receive password reset instructions shortly."
    )

    user = db.query(User).filter(User.email.ilike(clean_email)).first()
    if not user:
        return generic_response

    # Rate limiting: check if a reset was requested in the last 60 seconds
    now = datetime.now(timezone.utc)
    recent_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.user_id,
            PasswordResetToken.created_at >= now - timedelta(seconds=60)
        )
        .first()
    )
    if recent_token:
        # Rate limited: safely return the generic response without creating duplicates
        return generic_response

    # Invalidate any previous unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.is_used == False
    ).update({"is_used": True})

    # Generate high-entropy cryptographic token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = now + timedelta(minutes=15)

    reset_record = PasswordResetToken(
        user_id=user.user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
        created_at=now,
    )
    db.add(reset_record)
    db.commit()

    # Dispatch email (or log dev URL)
    EmailService.send_password_reset_email(
        recipient_email=user.email,
        reset_token=raw_token,
        user_name=user.full_name or user.email.split("@")[0]
    )

    return generic_response


@router.get(
    "/verify-reset-token",
    response_model=VerifyResetTokenResponse,
    summary="Validate password reset token status"
)
def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Validates if a password reset token is active, unexpired, and unused.
    """
    if not token or len(token.strip()) < 16:
        return VerifyResetTokenResponse(valid=False, message="Invalid or malformed reset token.")

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    reset_record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    if not reset_record:
        return VerifyResetTokenResponse(valid=False, message="Reset link is invalid.")

    if reset_record.is_used:
        return VerifyResetTokenResponse(valid=False, message="This reset link has already been used.")

    expires_at = reset_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        return VerifyResetTokenResponse(valid=False, message="Reset link has expired.")

    user = db.query(User).filter(User.user_id == reset_record.user_id).first()
    email_masked = None
    if user and user.email:
        parts = user.email.split("@")
        if len(parts[0]) > 2:
            email_masked = f"{parts[0][0]}***{parts[0][-1]}@{parts[1]}"
        else:
            email_masked = user.email

    return VerifyResetTokenResponse(valid=True, email=email_masked, message="Token is valid.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using a valid reset token"
)
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Consumes a valid password reset token and updates the user's password.
    Hashes the new password with bcrypt and immediately invalidates the token.
    """
    token_str = req.token.strip()
    if len(token_str) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or malformed reset token."
        )

    token_hash = hashlib.sha256(token_str.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    reset_record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    if not reset_record or reset_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link is invalid or has already been used."
        )

    expires_at = reset_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link has expired. Please request a new one."
        )

    user = db.query(User).filter(User.user_id == reset_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found."
        )

    # Update password securely with bcrypt
    user.hashed_password = hash_password(req.new_password)
    user.updated_at = now

    # Mark token used immediately (one-time use)
    reset_record.is_used = True

    db.commit()

    return MessageResponse(message="Password reset successfully. You can now sign in with your new password.")


@router.get(
    "/profile",
    response_model=CitizenProfileResponse,
    summary="Get current user's canonical citizen profile",
    description="Returns structured citizen profile, deterministic completion percentage, and annotated missing field list."
)
def get_auth_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns stored citizen profile for the authenticated user.
    If no profile has been created yet, returns an initialized empty profile.
    Strictly isolated: beneficiaries only access their own profile.
    """
    if current_user.profile_data:
        try:
            data = json.loads(current_user.profile_data)
            profile = BeneficiaryProfileInput(**data)
        except Exception:
            profile = BeneficiaryProfileInput()
    else:
        profile = BeneficiaryProfileInput()

    return calculate_profile_completion(profile)


@router.put(
    "/profile",
    response_model=CitizenProfileResponse,
    summary="Update citizen profile with strict backend validation",
    description="Validates and persists citizen profile parameters for deterministic eligibility and smart matching."
)
def update_auth_user_profile(
    profile_input: BeneficiaryProfileInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the authenticated user's citizen profile.
    Enforces validation on all numeric bounds (e.g. non-negative income, valid age).
    Handles partial and complete updates safely without data loss.
    Saves JSON snapshot in the database.
    Strictly isolated: beneficiaries only modify their own profile.
    """
    existing_data = {}
    if current_user.profile_data:
        try:
            existing_data = json.loads(current_user.profile_data)
        except Exception:
            existing_data = {}

    incoming_data = profile_input.model_dump(exclude_unset=True)
    updated_data = {**existing_data, **incoming_data}

    # Auto-align is_sc flag with social_category
    if "social_category" in updated_data and updated_data["social_category"]:
        cat = str(updated_data["social_category"]).upper()
        if cat == "SC":
            updated_data["is_sc"] = True
        elif cat in ["ST", "OBC", "GENERAL", "MINORITY"]:
            updated_data["is_sc"] = False

    validated_profile = BeneficiaryProfileInput(**updated_data)

    # Persist JSON serialized profile
    current_user.profile_data = json.dumps(validated_profile.model_dump())
    db.commit()
    db.refresh(current_user)

    return calculate_profile_completion(validated_profile)


# ─────────────────────────────────────────────────────────────
# Protected RBAC Test Endpoints (for RBAC testing)
# ─────────────────────────────────────────────────────────────

@router.get(
    "/test-beneficiary",
    summary="Beneficiary protected test endpoint"
)
def test_beneficiary_endpoint(
    current_user: User = Depends(require_roles(UserRole.BENEFICIARY, UserRole.SYSTEM_ADMIN))
):
    return {
        "status": "access_granted",
        "resource": "beneficiary_data",
        "user_id": current_user.user_id,
        "role": current_user.role
    }


@router.get(
    "/test-partner",
    summary="Partner user protected test endpoint"
)
def test_partner_endpoint(
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return {
        "status": "access_granted",
        "resource": "partner_assigned_data",
        "user_id": current_user.user_id,
        "role": current_user.role
    }


@router.get(
    "/test-partner-admin",
    summary="Partner admin protected test endpoint"
)
def test_partner_admin_endpoint(
    current_user: User = Depends(require_roles(UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return {
        "status": "access_granted",
        "resource": "partner_administration_data",
        "user_id": current_user.user_id,
        "role": current_user.role
    }


@router.get(
    "/test-system-admin",
    summary="System admin protected test endpoint"
)
def test_system_admin_endpoint(
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return {
        "status": "access_granted",
        "resource": "system_wide_administrative_data",
        "user_id": current_user.user_id,
        "role": current_user.role
    }
