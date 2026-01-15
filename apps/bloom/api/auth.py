"""
Authentication and Authorization

JWT-based authentication with role-based access control (RBAC).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel, Field

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "bloom-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for RBAC"""

    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR_ADMIN = "hr_admin"
    SYSTEM_ADMIN = "system_admin"


class TokenData(BaseModel):
    """JWT token payload data"""

    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: UserRole = Field(..., description="User role")
    exp: datetime = Field(..., description="Token expiration")
    iat: datetime = Field(..., description="Token issued at")


class User(BaseModel):
    """Authenticated user"""

    id: UUID
    email: str
    role: UserRole
    name: Optional[str] = None
    manager_id: Optional[UUID] = None


def create_access_token(
    user_id: UUID,
    email: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token

    Args:
        user_id: User's unique identifier
        email: User's email address
        role: User's role
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.utcnow()
    expire = now + expires_delta

    to_encode = {
        "user_id": str(user_id),
        "email": email,
        "role": role.value,
        "exp": expire,
        "iat": now,
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created access token for user {email} (role: {role})")

    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData object

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = UUID(payload.get("user_id"))
        email = payload.get("email")
        role = UserRole(payload.get("role"))
        exp = datetime.fromtimestamp(payload.get("exp"))
        iat = datetime.fromtimestamp(payload.get("iat"))

        return TokenData(
            user_id=user_id,
            email=email,
            role=role,
            exp=exp,
            iat=iat,
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token payload: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Dependency to get the current authenticated user

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = decode_token(token)

    # In production, you would fetch full user data from database here
    # For now, we'll construct it from token data
    user = User(
        id=token_data.user_id,
        email=token_data.email,
        role=token_data.role,
    )

    logger.debug(f"Authenticated user: {user.email} (role: {user.role})")
    return user


async def get_current_employee(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user is an employee or higher

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        HTTPException: If user doesn't have employee role or higher
    """
    allowed_roles = [
        UserRole.EMPLOYEE,
        UserRole.MANAGER,
        UserRole.HR_ADMIN,
        UserRole.SYSTEM_ADMIN,
    ]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: Employee role required",
        )

    return current_user


async def get_current_manager(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user is a manager or higher

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        HTTPException: If user doesn't have manager role or higher
    """
    allowed_roles = [UserRole.MANAGER, UserRole.HR_ADMIN, UserRole.SYSTEM_ADMIN]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: Manager role required",
        )

    return current_user


async def get_current_hr_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure current user is an HR admin or system admin

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        HTTPException: If user doesn't have HR admin role or higher
    """
    allowed_roles = [UserRole.HR_ADMIN, UserRole.SYSTEM_ADMIN]

    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: HR Admin role required",
        )

    return current_user


async def get_current_system_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure current user is a system admin

    Args:
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        HTTPException: If user doesn't have system admin role
    """
    if current_user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: System Admin role required",
        )

    return current_user


def check_evaluation_access(
    user: User,
    evaluation_employee_id: UUID,
    evaluation_manager_id: UUID,
    require_manager: bool = False,
) -> bool:
    """
    Check if user has access to an evaluation

    Args:
        user: Current user
        evaluation_employee_id: Employee being evaluated
        evaluation_manager_id: Manager conducting evaluation
        require_manager: If True, only manager/admin can access

    Returns:
        True if user has access

    Raises:
        HTTPException: If user doesn't have access
    """
    # System admins and HR admins can access all evaluations
    if user.role in [UserRole.SYSTEM_ADMIN, UserRole.HR_ADMIN]:
        return True

    # Manager access
    if user.id == evaluation_manager_id:
        return True

    # Employee access (only if not requiring manager)
    if not require_manager and user.id == evaluation_employee_id:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this evaluation",
    )


def check_peer_access(
    user: User,
    evaluation_approved_peers: list[UUID],
) -> bool:
    """
    Check if user is an approved peer for an evaluation

    Args:
        user: Current user
        evaluation_approved_peers: List of approved peer IDs

    Returns:
        True if user is an approved peer

    Raises:
        HTTPException: If user is not an approved peer
    """
    # System admins and HR admins can access
    if user.role in [UserRole.SYSTEM_ADMIN, UserRole.HR_ADMIN]:
        return True

    # Check if user is in approved peers list
    if user.id in evaluation_approved_peers:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not an approved peer reviewer for this evaluation",
    )


# ============================================================================
# Mock Authentication (for development/testing)
# ============================================================================


def create_mock_token(role: UserRole = UserRole.EMPLOYEE) -> str:
    """
    Create a mock token for development/testing

    Args:
        role: User role for the mock token

    Returns:
        JWT token string
    """
    from uuid import uuid4

    mock_user_id = uuid4()
    mock_email = f"mock.{role.value}@example.com"

    return create_access_token(
        user_id=mock_user_id,
        email=mock_email,
        role=role,
    )


# Example usage:
if __name__ == "__main__":
    # Create sample tokens
    employee_token = create_mock_token(UserRole.EMPLOYEE)
    manager_token = create_mock_token(UserRole.MANAGER)
    admin_token = create_mock_token(UserRole.HR_ADMIN)

    print("Sample Tokens:")
    print(f"\nEmployee Token:\n{employee_token}")
    print(f"\nManager Token:\n{manager_token}")
    print(f"\nAdmin Token:\n{admin_token}")

    # Decode and verify
    decoded = decode_token(employee_token)
    print(f"\nDecoded Token: {decoded}")
