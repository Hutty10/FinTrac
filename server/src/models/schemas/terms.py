from src.models.schemas.base import BaseSchemaModel


class TermsAcceptanceItem(BaseSchemaModel):
    terms_type: str  # "terms", "privacy_policy", "data_processing"
    version: str