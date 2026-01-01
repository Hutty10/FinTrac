from pydantic import ConfigDict, Field

from src.models.db.user_device import PlatformEnum
from src.models.schemas.base import BaseSchemaModel


class LoginDeviceSchema(BaseSchemaModel):
    device_id: str = Field(..., description="Stable client-generated device identifier")
    device_name: str | None = Field(None, description="Human readable device name")
    platform: PlatformEnum
    os_version: str | None = None
    app_version: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "ios-uuid-123456",
                "device_name": "iPhone 14 Pro",
                "platform": "ios",
                "os_version": "17.2",
                "app_version": "1.0.3",
            }
        }
    )


class LoginContextSchema(BaseSchemaModel):
    ip_address: str | None = None
    user_agent: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ip_address": "197.210.12.45",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            }
        }
    )
