"""FastAPI dependency helpers for authentication and authorization."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, UserRole
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

Role = UserRole

_db = Annotated[Session, Depends(get_db)]


def _extract_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: _db,
) -> User:
    """Return the authenticated user for the current request."""
    payload = _extract_payload(credentials)
    user_id = payload.get("uid")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


UserDep = Annotated[User, Depends(current_user)]


def require_role(*roles: UserRole):
    """Return a dependency factory enforcing one of the given roles."""

    def _checker(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _checker


AdminDep = Annotated[User, Depends(require_role(UserRole.ADMIN))]
AnalystDep = Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.ANALYST))]