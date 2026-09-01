import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    GoogleLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)
from app.schemas.profile import (
    BeneficiaryProfileInput,
    CitizenProfileResponse,
    calculate_profile_completion,
)
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
