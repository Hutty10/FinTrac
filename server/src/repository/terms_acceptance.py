from src.models.db.terms_acceptance import TermsAcceptance
from src.repository.base import BaseRepository


class TermsAcceptanceRepository(BaseRepository[TermsAcceptance]):
    def __init__(self):
        super().__init__(TermsAcceptance)
