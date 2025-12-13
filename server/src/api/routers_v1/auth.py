from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.models.schemas.auth import (
    ForgotPasswordSchema,
    LoginSchema,
    LogoutSchema,
    RefreshTokenSchema,
    RegisterUserSchema,
    ResendVerificationEmailSchema,
    ResetPasswordSchema,
    TokenSchema,
    VerifyEmailSchema,
    VerifyPasswordResetSchema,
)
from src.models.schemas.response import ResponseModel
from src.service.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=ResponseModel[None], status_code=status.HTTP_201_CREATED
)
async def register_user(
    data: RegisterUserSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel[None]:
    return await auth_service.register_user(session, data)


@router.post("/verify-email", response_model=ResponseModel)
async def verify_email(
    data: VerifyEmailSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel:
    return await auth_service.verify_email(session, data)


@router.post("/resend-verification-email", response_model=ResponseModel)
async def resend_verification_email(
    data: ResendVerificationEmailSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel:
    return await auth_service.resend_verification_email(session, data)


@router.post("/login", response_model=ResponseModel[TokenSchema])
async def login(
    data: LoginSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel[TokenSchema]:
    return await auth_service.login_user(session, data)


@router.post("/refresh-token", response_model=ResponseModel[TokenSchema])
async def refresh_token(
    data: RefreshTokenSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel[TokenSchema]:
    return await auth_service.refresh_tokens(session, data)


@router.post("/forgot-password", response_model=ResponseModel)
async def forgot_password(
    data: ForgotPasswordSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel:
    return await auth_service.forgot_password(session, data)


@router.post("/verify-password-reset", response_model=ResponseModel[dict[str, str]])
async def verify_password_reset(
    data: VerifyPasswordResetSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel[dict[str, str]]:
    return await auth_service.verify_password_reset_otp(session, data)


@router.post("/reset-password", response_model=ResponseModel)
async def reset_password(
    data: ResetPasswordSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel:
    return await auth_service.reset_password(session, data)


@router.post("/logout", response_model=ResponseModel)
async def logout(
    data: LogoutSchema,
    session: AsyncSession = Depends(get_session),
) -> ResponseModel:
    return await auth_service.logout_user(session, data)
