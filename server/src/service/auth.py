import logging
import time
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.manager import settings
from src.core.securities.jwt import jwt_manager
from src.core.tasks.email_tasks import (
    send_password_reset_email_task,
    send_verification_email_task,
)
from src.core.utils.exceptions.base import BaseAppException
from src.core.utils.messages.exceptions.http import exc_details
from src.models.db.account import Account, AccountType
from src.models.db.otp import OTPType
from src.models.db.streak import Streak
from src.models.db.terms_acceptance import TermsAcceptance
from src.models.db.user import User
from src.models.db.user_pref import UserPreference
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
from src.repository.account import AccountRepository
from src.repository.currency import CurrencyRepository
from src.repository.otp import OTPRepository
from src.repository.streak import StreakRepository
from src.repository.terms_acceptance import TermsAcceptanceRepository
from src.repository.user import UserRepository
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
        super().__init__(repo)

    async def register_user(
        self, session: AsyncSession, user_data: RegisterUserSchema
    ) -> ResponseModel[None]:
        """Register a new user"""
        start = time.time()
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
        )
        default_currency_id = user_pref.default_currency_id
        await self.user_pref_repo.create(session, user_pref)

        for term_item in user_data.accepted_terms:
            term = TermsAcceptance(
                user_id=new_user.id,
                terms_version=f"{term_item.terms_type}:{term_item.version}",
                ip_address=user_data.ip_address,
                device_info=user_data.device_info,
            )
            await self.terms_acceptance_repo.create(session, term)
        else:
            logger.error("No error accepting terms")

        streak = Streak(user_id=new_user.id)
        await self.streak_repo.create(session, streak)

        account = Account(
            user_id=new_user.id,
            name="main",
            account_type=AccountType.BANK,
            currency_id=default_currency_id,
        )
        await self.account_repo.create(session, account)

        # otp_code = self.otp_repo.generate_otp_code()
        # otp_expires_at = datetime.now(timezone.utc) + timedelta(
        #     minutes=settings.OTP_EXPIRY_MINUTES
        # )
        # otp = OTP(
        #     user_id=user_id,
        #     code=otp_code,
        #     type=OTPType.EMAIL_VERIFICATION,
        #     expires_at=otp_expires_at,
        # )
        otp = await self.otp_repo.create_otp(
            session,
            new_user.id,
            OTPType.EMAIL_VERIFICATION,
            settings.OTP_EXPIRY_MINUTES,
        )
        before_send_time = time.time()
        print(f"Time before sending email: {before_send_time - start:.4f} seconds")

        send_verification_email_task.delay(
            recipient_email=new_user.email,
            recipient_name=new_user.first_name,
            code=otp.code,
            expiry=settings.OTP_EXPIRY_MINUTES,
        )
        time_after_sending = time.time()
        print(f"Time taken to register user: {time_after_sending - start:.4f} seconds")
        print(
            f"Time after sending email: {time_after_sending - before_send_time:.4f} seconds"
        )

        return ResponseModel(
            message="User registered successfully check your email for verification",
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
    ) -> ResponseModel[TokenSchema]:
        """Authenticate user and return JWT tokens"""
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
        is_password_valid = user.verify_password(data.password)
        if not is_password_valid:
            raise BaseAppException(
                message=exc_details.http_400_signin_credentials_details(),
                status_code=400,
            )
        tokens = await user.tokens
        await self.repository.update_last_login(session, user)
        return ResponseModel(
            message="Login successful",
            data=TokenSchema(**tokens),
        )

    async def refresh_tokens(
        self, session: AsyncSession, data: RefreshTokenSchema
    ) -> ResponseModel[TokenSchema]:
        """Refresh JWT tokens using refresh token"""
        token = await jwt_manager.refresh_access_token(data.refresh_token, data.rotate)
        return ResponseModel(
            message="Token refreshed successfully", data=TokenSchema(**token)
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
        await self.otp_repo.delete(session, otp.id)
        return ResponseModel(
            message="Password has been reset successfully proceed to login", data=None
        )

    async def logout_user(
        self, session: AsyncSession, data: LogoutSchema
    ) -> ResponseModel[None]:
        """Logout user by invalidating the refresh token"""
        try:
            await jwt_manager.blacklist_refresh_token(data.refresh_token)
            # Here you would invalidate the token in your storage
            logger.info(
                f"User with refresh token {data.refresh_token} logged out successfully."
            )
        except BaseAppException as e:
            raise e
        return ResponseModel(message="Logout successful", data=None)


auth_service = AuthService()
