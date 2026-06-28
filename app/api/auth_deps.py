from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import get_account_repo, get_auth_service
from app.core.constants import UserRole
from app.core.schemas.auth import UserInDB
from app.repositories.account_repository import AccountRepository
from app.services.auth.service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> UserInDB | None:
    if credentials is None:
        return None
    try:
        return await auth.get_user_from_token(credentials.credentials)
    except ValueError:
        return None


async def get_current_user(
    user: Annotated[UserInDB | None, Depends(get_current_user_optional)],
) -> UserInDB:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


CurrentUserDep = Annotated[UserInDB, Depends(get_current_user)]
CurrentUserOptionalDep = Annotated[UserInDB | None, Depends(get_current_user_optional)]
AdminUserDep = Annotated[UserInDB, Depends(require_admin)]
AccountRepoDep = Annotated[AccountRepository, Depends(get_account_repo)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
