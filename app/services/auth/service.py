from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.config import Settings
from app.core.constants import UserRole
from app.core.schemas.auth import TokenResponse, UserInDB, UserResponse
from app.repositories.account_repository import AccountRepository


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def create_access_token(settings: Settings, user_id: str, role: UserRole) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(settings: Settings, token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


class AuthService:
    def __init__(self, settings: Settings, accounts: AccountRepository) -> None:
        self._settings = settings
        self._accounts = accounts

    async def register(self, email: str, password: str) -> UserResponse:
        existing = await self._accounts.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        user_id = await self._accounts.create(email, hash_password(password))
        doc = await self._accounts.get_by_id(user_id)
        if not doc:
            raise RuntimeError("Failed to create user")
        return self._to_response(doc)

    async def authenticate(self, email: str, password: str) -> UserInDB:
        doc = await self._accounts.get_by_email(email)
        if not doc or not verify_password(password, doc["password_hash"]):
            raise ValueError("Invalid email or password")
        if not doc.get("is_active", True):
            raise ValueError("Account is disabled")
        return AccountRepository.to_user(doc)

    async def get_user_from_token(self, token: str) -> UserInDB:
        try:
            payload = decode_access_token(self._settings, token)
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token")
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc

        doc = await self._accounts.get_by_id(str(user_id))
        if not doc or not doc.get("is_active", True):
            raise ValueError("User not found")
        return AccountRepository.to_user(doc)

    def issue_token(self, user: UserInDB) -> TokenResponse:
        access_token = create_access_token(self._settings, user.id, user.role)
        return TokenResponse(
            access_token=access_token,
            user=self._user_to_response(user),
        )

    async def ensure_bootstrap_admin(self) -> None:
        email = self._settings.auth_admin_email.strip()
        password = self._settings.auth_admin_password
        if not email or not password:
            return
        await self._accounts.upsert_bootstrap_admin(email, hash_password(password))

    @staticmethod
    def _to_response(doc: dict) -> UserResponse:
        return AuthService._user_to_response(AccountRepository.to_user(doc))

    @staticmethod
    def _user_to_response(user: UserInDB) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )
