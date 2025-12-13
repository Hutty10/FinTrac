import random
import string
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.db.otp import OTP, OTPType
from src.repository.base import BaseRepository


class OTPRepository(BaseRepository[OTP]):
    def __init__(self):
        super().__init__(OTP)

    def generate_otp_code(self, length: int = 6) -> str:
        """Generate a random OTP code with digits and letters"""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    async def get_valid_otp(
        self, session: AsyncSession, user_id: UUID, code: str, otp_type: OTPType
    ) -> OTP | None:
        """Get a valid OTP for a user by code"""
        statement = select(self.model).where(
            (self.model.user_id == user_id)
            & (self.model.code == code)
            & (self.model.type == otp_type)
            & (~self.model.is_used)  # type: ignore
            & (self.model.expires_at > func.now())  # type: ignore
        )
        result = await session.exec(statement)
        otp = result.first()
        print("result:", otp)
        return otp

    async def create_otp(
        self,
        session: AsyncSession,
        user_id: UUID,
        otp_type: OTPType,
        expiry_minutes: int = 10,
    ) -> OTP:
        """Create and return a new OTP for a user"""
        statement = select(self.model).where(
            (self.model.user_id == user_id) & (self.model.type == otp_type)
        )
        result = await session.exec(statement)
        existing_otps = result.all()
        for otp in existing_otps:
            await session.delete(otp)
        code = self.generate_otp_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
        otp = OTP(user_id=user_id, type=otp_type, code=code, expires_at=expires_at)
        session.add(otp)
        await session.commit()
        await session.refresh(otp)
        return otp
