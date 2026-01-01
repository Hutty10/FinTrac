import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.manager import settings
from src.core.securities.jwt import jwt_manager
from src.core.tasks.email_tasks import (
    send_new_device_login_alert,
    send_password_reset_email_task,
    send_verification_email_task,
)
from src.core.utils.exceptions.base import BaseAppException
from src.core.utils.messages.exceptions.http import exc_details
from src.core.utils.user_utils import check_deleted_user
from src.models.db.account import Account, AccountType
from src.models.db.auth_session import AuthSession
from src.models.db.otp import OTPType
from src.models.db.security_event import SecurityEvent, SecurityEventTypeEnum
from src.models.db.streak import Streak
from src.models.db.terms_acceptance import TermsAcceptance
from src.models.db.user import User
from src.models.db.user_device import UserDevice
from src.models.db.user_pref import UserPreference
from src.models.schemas.auth import (
    ForgotPasswordSchema,
    LoginDeviceResponseSchema,
    LoginResponse,
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
from src.models.schemas.mails import NewDeviceLoginAlertSchema
from src.models.schemas.response import ResponseModel
from src.repository.account import AccountRepository
from src.repository.auth_session import AuthSessionRepository
from src.repository.currency import CurrencyRepository
from src.repository.otp import OTPRepository
from src.repository.security_event import SecurityEventRepository
from src.repository.streak import StreakRepository
from src.repository.terms_acceptance import TermsAcceptanceRepository
from src.repository.user import UserRepository
from src.repository.user_device import UserDeviceRepository
from src.repository.user_pref import UserPrefRepository
from src.service.base import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService[User, UserRepository]):
    """Service class for authentication-related operations"""

    def __init__(self):
        repo = UserRepository()
        self.user_pref_repo = UserPrefRepository()
        self.currency_repo = CurrencyRepository()
        self.terms_acceptance_repo = TermsAcceptanceRepository()
        self.streak_repo = StreakRepository()
        self.account_repo = AccountRepository()
        self.otp_repo = OTPRepository()
        self.device_repo = UserDeviceRepository()
        self.auth_session_repo = AuthSessionRepository()
        self.security_event_repo = SecurityEventRepository()
        super().__init__(repo)

    async def register_user(
        self, session: AsyncSession, user_data: RegisterUserSchema
    ) -> ResponseModel[None]:
        start = time.time()

        # ---------- VALIDATIONS ----------
        if not user_data.accept_terms:
            raise BaseAppException(
                message="Terms must be accepted to register",
                status_code=400,
            )

        existing_user = await self.repository.get_by_email(session, user_data.email)
        if existing_user:
            raise BaseAppException(
                message=exc_details.http_400_email_details(user_data.email),
                status_code=400,
            )

        if user_data.username:
            existing_user = await self.repository.get_by_username(
                session, user_data.username
            )
            if existing_user:
                raise BaseAppException(
                    message=exc_details.http_400_username_details(user_data.username),
                    status_code=400,
                )

        # ---------- CREATE USER ----------
        role_id = await self.repository.get_user_role_id(session)
        new_user: User = User(
            role_id=role_id,
            **user_data.model_dump(
                exclude={"password", "accept_terms", "accepted_terms"}
            ),
        )
        new_user.set_password(user_data.password)

        new_user = await self.repository.create(session, new_user)
        await session.refresh(new_user)

        # ---------- USER PREFERENCES ----------
        default_currency = await self.currency_repo.get_by_code(session, "NGN")
        if not default_currency:
            raise BaseAppException(
                message="Default currency not found",
                status_code=500,
            )

        user_pref = UserPreference(
            user_id=new_user.id,
            locale=user_data.prefered_locale,
            theme=user_data.theme,
            default_currency_id=default_currency.id,
            notifications_enabled=True,
        )
        await self.user_pref_repo.create(session, user_pref)

        # ---------- TERMS ACCEPTANCE ----------
        ip_address = user_data.context.ip_address if user_data.context else "unknown"
        device_id = user_data.device.device_id

        for term_item in user_data.accepted_terms:
            term = TermsAcceptance(
                user_id=new_user.id,
                terms_version=f"{term_item.terms_type}:{term_item.version}",
                ip_address=ip_address,
                device_info=device_id,
            )
            await self.terms_acceptance_repo.create(session, term)

        # ---------- STREAK ----------
        streak = Streak(user_id=new_user.id)
        await self.streak_repo.create(session, streak)

        # ---------- DEVICE REGISTRATION ----------
        existing_device = await self.device_repo.get_by_device_id(
            session,
            new_user.id,
            user_data.device.device_id,
        )

        if not existing_device:
            device = UserDevice(
                user_id=new_user.id,
                device_id=user_data.device.device_id,
                device_name=user_data.device.device_name,
                platform=user_data.device.platform,
                os_version=user_data.device.os_version,
                app_version=user_data.device.app_version,
                is_trusted=False,
            )
            await self.device_repo.create(session, device)

        # ---------- DEFAULT ACCOUNT ----------
        account = Account(
            user_id=new_user.id,
            name="Main Account",
            account_type=AccountType.BANK,
            currency_id=default_currency.id,
        )
        await self.account_repo.create(session, account)

        # ---------- EMAIL VERIFICATION OTP ----------
        otp = await self.otp_repo.create_otp(
            session,
            new_user.id,
            OTPType.EMAIL_VERIFICATION,
            settings.OTP_EXPIRY_MINUTES,
        )

        send_verification_email_task.delay(
            recipient_email=new_user.email,
            recipient_name=new_user.first_name,
            code=otp.code,
            expiry=settings.OTP_EXPIRY_MINUTES,
        )

        logger.info(
            f"User registration completed in {time.time() - start:.2f}s "
            f"(user_id={new_user.id})"
        )

        return ResponseModel(
            message="User registered successfully. Please verify your email.",
            data=None,
        )

    async def verify_email(
        self, session: AsyncSession, data: VerifyEmailSchema
    ) -> ResponseModel:
        """Verify user's email using OTP code"""
        user = await self.repository.get_by_email(session, data.email)
        if not user:
            raise BaseAppException(
                message="Wrong email address provided",
                status_code=400,
            )
        if user.is_verified:
            raise BaseAppException(
                message="Email is already verified",
                status_code=400,
            )
        otp = await self.otp_repo.get_valid_otp(
            session, user.id, data.code, OTPType.EMAIL_VERIFICATION
        )
        if not otp:
            raise BaseAppException(
                message="Invalid or expired verification code",
                status_code=400,
            )
        await self.repository.update(session, user.id, {"is_verified": True})
        await self.otp_repo.delete(session, otp.id)
        return ResponseModel(
            message="Email verified successfully proceed to login", data=None
        )

    async def resend_verification_email(
        self, session: AsyncSession, data: ResendVerificationEmailSchema
    ) -> ResponseModel:
        """Resend verification email to user"""
        user = await self.repository.get_by_email(session, data.email)
        if user:
            # otp_code = self.otp_repo.generate_otp_code()
            # otp_expires_at = datetime.now(timezone.utc) + timedelta(
            #     minutes=settings.OTP_EXPIRY_MINUTES
            # )
            # otp = OTP(
            #     user_id=user.id,
            #     code=otp_code,
            #     type=OTPType.EMAIL_VERIFICATION,
            #     expires_at=otp_expires_at,
            # )
            if user.is_deleted:
                check_deleted_user(user)
            otp = await self.otp_repo.create_otp(
                session,
                user.id,
                OTPType.EMAIL_VERIFICATION,
                settings.OTP_EXPIRY_MINUTES,
            )
            send_verification_email_task.delay(
                recipient_email=user.email,
                recipient_name=user.first_name,
                code=otp.code,
                expiry=settings.OTP_EXPIRY_MINUTES,
            )
        return ResponseModel(
            message="If an account exists, a verification email will be sent", data=None
        )

    async def login_user(
        self, session: AsyncSession, data: LoginSchema
    ) -> ResponseModel[LoginResponse]:
        user: User | None = None

        if data.email:
            user = await self.repository.get_by_email(session, data.email)
        elif data.username:
            user = await self.repository.get_by_username(session, data.username)

        if not user:
            raise BaseAppException(
                message="Invalid email/username or password",
                status_code=401,
            )

        if user.is_deleted:
            check_deleted_user(user)

        if not user.verify_password(data.password):
            raise BaseAppException(
                message=exc_details.http_400_signin_credentials_details(),
                status_code=400,
            )

        # ---- DEVICE HANDLING ----
        device = await self.device_repo.get_by_device_id(
            session,
            user.id,
            data.device.device_id,
        )

        if not device:
            device = UserDevice(
                user_id=user.id,
                device_id=data.device.device_id,
                device_name=data.device.device_name,
                platform=data.device.platform,
                os_version=data.device.os_version,
                app_version=data.device.app_version,
                is_trusted=False,
            )
            device = await self.device_repo.create(session, device)

            security_event = SecurityEvent(
                user_id=user.id,
                event_type=SecurityEventTypeEnum.NEW_DEVICE_LOGIN,
                ip_address=data.context.ip_address if data.context else None,
                user_agent=data.context.user_agent if data.context else None,
                meta={
                    "device_id": data.device.device_id,
                    "device_name": data.device.device_name,
                    "platform": data.device.platform,
                    "os_version": data.device.os_version,
                    "app_version": data.device.app_version,
                },
            )
            await self.security_event_repo.create(session, security_event)
            print("sending email")
            data = NewDeviceLoginAlertSchema(
                device_name=device.device_name,  # type: ignore
                operating_system=device.platform.capitalize(),
                ip_address=data.context.ip_address if data.context else None,
                login_time=datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p"),
                secure_account_url="https://fintrac.app/security",
                support_url="https://fintrac.app/support",
                security_url="https://fintrac.app/security",
                settings_url="https://fintrac.app/settings",
            )
            send_new_device_login_alert.delay(
                recipient_email=user.email,
                recipient_name=user.first_name,
                data=data.model_dump(),
            )
            print("done sending email")

        else:
            device.last_login_at = datetime.now(timezone.utc)
            await self.device_repo.update(
                session, device.id, {"last_login_at": device.last_login_at}
            )

        requires_device_verification = not device.is_trusted

        await self.auth_session_repo.revoke_by_device(session, user.id, device.id)

        # ---- TOKENS ----
        tokens = await user.tokens
        # tokens = await jwt_manager.create_token_pair(user_id=user.id)
        refresh_jti = await jwt_manager.extract_jti(tokens["refresh_token"])

        # ---------- AUTH SESSION ----------
        active_sessions = await self.auth_session_repo.count_active_sessions(
            session,
            user.id,
        )
        MAX_SESSIONS = settings.MAX_SESSIONS_PER_USER
        if active_sessions >= MAX_SESSIONS:
            excess = (active_sessions + 1) - MAX_SESSIONS

            await self.auth_session_repo.revoke_oldest_sessions(
                session=session,
                user_id=user.id,
                limit=excess,
            )
            security_event = SecurityEvent(
                user_id=user.id,
                event_type=SecurityEventTypeEnum.SESSION_INVALIDATED,
                ip_address=data.context.ip_address if data.context else None,
                user_agent=data.context.user_agent if data.context else None,
                meta={
                    "reason": "MAX_CONCURRENT_SESSIONS_EXCEEDED",
                    "evicted_sessions": excess,
                },
            )
            await self.security_event_repo.create(session, security_event)

        expires_at = await jwt_manager.extract_exp(
            tokens["refresh_token"], token_type="refresh"
        )
        auth_session = AuthSession(
            user_id=user.id,
            device_id=device.id,
            refresh_token_jti=refresh_jti,
            expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
        )
        await self.auth_session_repo.create(session, auth_session)

        await self.repository.update_last_login(session, user)

        return ResponseModel(
            message="Login successful",
            data=LoginResponse(
                user_id=user.id,
                tokens=TokenSchema(
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                ),
                device=LoginDeviceResponseSchema(
                    id=device.id,
                    is_trusted=device.is_trusted,
                    last_login_at=device.last_login_at,
                ),
                requires_device_verification=requires_device_verification,
            ),
        )

    async def refresh_tokens(
        self, session: AsyncSession, data: RefreshTokenSchema
    ) -> ResponseModel[TokenSchema]:
        """Refresh JWT tokens using refresh token"""
        jti = await jwt_manager.extract_jti(data.refresh_token)

        auth_session = await self.auth_session_repo.get_active_by_jti(session, jti)
        if not auth_session:
            raise BaseAppException(
                message="Invalid or expired refresh token",
                status_code=401,
            )

        if not auth_session.is_active or auth_session.expires_at <= datetime.now(
            timezone.utc
        ):
            raise BaseAppException(
                message="Refresh token session expired or revoked",
                status_code=401,
            )

        tokens = await jwt_manager.refresh_access_token(data.refresh_token, data.rotate)

        if data.rotate:
            auth_session.refresh_token_jti = await jwt_manager.extract_jti(
                tokens["refresh_token"]
            )

        await self.auth_session_repo.touch(session, auth_session)

        return ResponseModel(
            message="Token refreshed successfully", data=TokenSchema(**tokens)
        )

    async def forgot_password(
        self, session: AsyncSession, data: ForgotPasswordSchema
    ) -> ResponseModel:
        """Handle forgot password by sending OTP to user's email"""
        user: User | None = None
        if data.email:
            user = await self.repository.get_by_email(session, data.email)
        elif data.username:
            user = await self.repository.get_by_username(session, data.username)
        if user:
            # otp_code = self.otp_repo.generate_otp_code()
            # otp_expires_at = datetime.now(timezone.utc) + timedelta(
            #     minutes=settings.OTP_EXPIRY_MINUTES
            # )
            # otp = OTP(
            #     user_id=user.id,
            #     code=otp_code,
            #     type=OTPType.PASSWORD_RESET,
            #     expires_at=otp_expires_at,
            # )
            if user.is_deleted:
                check_deleted_user(user)
            otp = await self.otp_repo.create_otp(
                session,
                user.id,
                OTPType.PASSWORD_RESET,
                settings.OTP_EXPIRY_MINUTES,
            )
            send_password_reset_email_task.delay(
                recipient_email=user.email,
                recipient_name=user.first_name,
                code=otp.code,
                expiry=settings.OTP_EXPIRY_MINUTES,
            )
        return ResponseModel(
            message="If an account exists, a password reset email will be sent",
            data=None,
        )

    async def verify_password_reset_otp(
        self, session: AsyncSession, data: VerifyPasswordResetSchema
    ) -> ResponseModel[dict[str, str]]:
        """Verify OTP for password reset"""
        user: User | None = None
        if data.email:
            user = await self.repository.get_by_email(session, data.email)
        elif data.username:
            user = await self.repository.get_by_username(session, data.username)
        if not user:
            raise BaseAppException(
                message="Wrong email address or username provided",
                status_code=400,
            )
        otp = await self.otp_repo.get_valid_otp(
            session, user.id, data.code, OTPType.PASSWORD_RESET
        )
        if not otp:
            raise BaseAppException(
                message="Invalid or expired password reset code",
                status_code=400,
            )
        return ResponseModel(
            message="OTP verified successfully", data={"token": otp.id.hex}
        )

    async def reset_password(
        self, session: AsyncSession, data: ResetPasswordSchema
    ) -> ResponseModel:
        """Reset user's password using OTP token"""
        user: User | None = None
        if data.email:
            user = await self.repository.get_by_email(session, data.email)
        elif data.username:
            user = await self.repository.get_by_username(session, data.username)
        if not user:
            raise BaseAppException(
                message="Wrong email address or username provided",
                status_code=400,
            )
        if user.is_deleted:
            check_deleted_user(user)
        otp = await self.otp_repo.get_by_id(session, UUID(data.token))
        if not otp or otp.user_id != user.id or otp.type != OTPType.PASSWORD_RESET:
            raise BaseAppException(
                message="Invalid password reset token",
                status_code=400,
            )
        # if otp.expires_at < datetime.now(timezone.utc):
        #     raise BaseAppException(
        #         message="Password reset token has expired",
        #         status_code=400,
        #     )
        user.set_password(data.new_password)
        await self.repository.update(
            session, user.id, {"hashed_password": user.hashed_password}
        )

        security_event = SecurityEvent(
            user_id=user.id,
            event_type=SecurityEventTypeEnum.NEW_DEVICE_LOGIN,
            ip_address=data.context.ip_address if data.context else None,
            user_agent=data.context.user_agent if data.context else None,
            meta={
                "device_id": data.device.device_id,
                "device_name": data.device.device_name,
                "platform": data.device.platform,
                "os_version": data.device.os_version,
                "app_version": data.device.app_version,
            },
        )
        await self.security_event_repo.create(session, security_event)

        await self.otp_repo.delete(session, otp.id)

        return ResponseModel(
            message="Password has been reset successfully proceed to login", data=None
        )

    async def logout_user(
        self, session: AsyncSession, data: LogoutSchema
    ) -> ResponseModel[None]:
        """Logout user by invalidating the refresh token"""

        jti = await jwt_manager.extract_jti(data.refresh_token)

        auth_session = await self.auth_session_repo.get_active_by_jti(session, jti)
        if auth_session:
            await self.auth_session_repo.revoke(session, auth_session)

        await jwt_manager.blacklist_refresh_token(data.refresh_token)

        logger.info(
            f"User with refresh token {data.refresh_token} logged out successfully."
        )

        return ResponseModel(message="Logout successful", data=None)


auth_service = AuthService()
