from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)

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
