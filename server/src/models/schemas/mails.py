from src.models.schemas.base import BaseSchemaModel


class NewDeviceLoginAlertSchema(BaseSchemaModel):
    device_name: str
    operating_system: str
    ip_address: str | None
    login_time: str
    secure_account_url: str
    support_url: str
    security_url: str
    settings_url: str
