from typing import Generator, List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

# HTTP Bearer scheme for token extraction
security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: Union[HTTPAuthorizationCredentials, None] = Depends(security_bearer)
) -> User:
    """
    Dependency that extracts the Bearer JWT token from the Authorization header,
    validates the token, and retrieves the active user from the database.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Union[HTTPAuthorizationCredentials, None] = Depends(security_bearer)
) -> Union[User, None]:
    """
    Optional dependency that returns the active user if a valid Bearer token is provided,
    or None for unauthenticated public requests.
    """
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id:
            return db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
    except Exception:
        pass
    return None


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency ensuring the user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return current_user


class RoleChecker:
    """
    Reusable Dependency Factory for Role-Based Access Control (RBAC).
    Enforces role authorization server-side.
    """
    def __init__(self, allowed_roles: List[Union[str, UserRole]]):
        self.allowed_roles = [
            r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles
        ]

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized to access this resource. Required role(s): {self.allowed_roles}"
            )
        return current_user


def require_roles(*roles: Union[str, UserRole]) -> RoleChecker:
    """
    Helper function returning a RoleChecker dependency.
    Example: Depends(require_roles(UserRole.BENEFICIARY, UserRole.SYSTEM_ADMIN))
    """
    return RoleChecker(list(roles))
