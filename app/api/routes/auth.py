from fastapi import APIRouter, HTTPException, status

from app.api.auth_deps import AuthServiceDep, CurrentUserDep
from app.core.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, auth: AuthServiceDep) -> TokenResponse:
    try:
        await auth.register(body.email, body.password)
        user = await auth.authenticate(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return auth.issue_token(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, auth: AuthServiceDep) -> TokenResponse:
    try:
        user = await auth.authenticate(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return auth.issue_token(user)


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUserDep) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )
