"""
Auth Service — JWT Authentication & Authorization Microservice
"""

from __future__ import annotations

import sys
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

sys.path.insert(0, "/app")
from shared.common.exceptions import (
    BaseServiceError,
    ConflictError,
    UnauthorizedError,
)
from shared.common.logging import configure_logging, get_logger
from shared.common.schemas import (
    APIResponse,
    ErrorResponse,
    HealthResponse,
    ServiceName,
    TokenResponse,
    UserCreate,
    UserResponse,
)


# ── Settings ──
class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "auth-service"
    environment: str = "development"
    log_level: str = "INFO"
    auth_port: int = 8001
    version: str = "0.1.0"

    database_url: str = "postgresql+asyncpg://app_user:password@postgres:5432/scalable_ai"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str = "CHANGE_ME_jwt_secret_minimum_32_chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7


settings = AuthSettings()

# ── Database ──
is_test = settings.environment == "testing" or "pytest" in sys.modules
if is_test:
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        connect_args={"timeout": 2},
    )
else:
    engine = create_async_engine(
        settings.database_url,
        pool_size=10,
        pool_pre_ping=True,
    )
session_factory = async_sessionmaker(engine, expire_on_commit=False)


_start_time: float = 0.0

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── JWT Helpers ──
def create_token(user_id: str, role: str, expires_delta: timedelta) -> str:
    """Create a JWT token."""
    import jwt as pyjwt

    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    import jwt as pyjwt

    try:
        payload = pyjwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired") from None
    except pyjwt.InvalidTokenError:
        raise UnauthorizedError("Invalid token") from None


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _start_time

    configure_logging(
        settings.service_name, settings.log_level, json_format=settings.environment != "development"
    )
    logger = get_logger(__name__)
    logger.info("Starting Auth Service", version=settings.version)
    _start_time = time.time()

    # Verify DB connection
    if settings.environment != "testing":
        try:
            async with engine.begin() as conn:
                from sqlalchemy import text

                await conn.execute(text("SELECT 1"))
        except Exception as e:  # noqa: BLE001
            logger.warning("Database not available on startup", error=str(e))
    logger.info("Auth Service started")

    yield

    logger.info("Auth Service stopping")
    if not ("pytest" in sys.modules or settings.environment == "testing"):
        with suppress(Exception):
            await engine.dispose()


# ── App ──
app = FastAPI(
    title="Auth Service",
    description="JWT Authentication & Authorization",
    version=settings.version,
    lifespan=lifespan,
)


# ── Error Handlers ──
@app.exception_handler(BaseServiceError)
async def service_error_handler(request: Request, exc: BaseServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error_code, detail=exc.message).model_dump(mode="json"),
    )


# ── Health ──
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        service=ServiceName.AUTH,
        version=settings.version,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


# ── Auth Endpoints ──
@app.post(
    "/auth/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate) -> APIResponse[UserResponse]:
    """Register a new user."""
    logger = get_logger(__name__)

    async with session_factory() as session:
        # Import User model inline to avoid circular imports
        from app.models import User

        # Check existing
        result = await session.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise ConflictError(f"Email '{user_data.email}' is already registered")

        # Create user (TODO: proper argon2 hashing)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=f"argon2hash_{user_data.password}",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.info("User registered", user_id=str(user.id))

        return APIResponse(
            data=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at,
            ),
            message="Registration successful",
        )


@app.post("/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """Authenticate user and issue JWT tokens."""
    logger = get_logger(__name__)

    async with session_factory() as session:
        from app.models import User

        result = await session.execute(select(User).where(User.email == form_data.username))
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedError("Invalid credentials")

        # TODO: verify with argon2
        if user.hashed_password != f"argon2hash_{form_data.password}":
            raise UnauthorizedError("Invalid credentials")

        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        # Issue tokens
        access_token = create_token(
            user_id=str(user.id),
            role=user.role,
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        )
        refresh_token = create_token(
            user_id=str(user.id),
            role=user.role,
            expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
        )

        logger.info("User logged in", user_id=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(token: str = Depends(oauth2_scheme)) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    payload = verify_token(token)

    access_token = create_token(
        user_id=payload["sub"],
        role=payload.get("role", "user"),
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    refresh = create_token(
        user_id=payload["sub"],
        role=payload.get("role", "user"),
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@app.get("/auth/me", response_model=APIResponse[UserResponse])
async def get_current_user(token: str = Depends(oauth2_scheme)) -> APIResponse[UserResponse]:
    """Get current authenticated user."""
    payload = verify_token(token)

    async with session_factory() as session:
        from app.models import User

        result = await session.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedError("User not found")

        return APIResponse(
            data=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                role=user.role,
                created_at=user.created_at,
            ),
        )
