# Import base/reference models first (no dependencies on other models)
from src.models.db.currency import Currency  # noqa: I001
from src.models.db.permission import Role, Permission, RolePermission
from src.models.db.otp import OTP

# Then import models that reference User (but User isn't imported yet)
from src.models.db.account import Account
from src.models.db.category import Category
from src.models.db.budget import Budget
from src.models.db.goal import Goal
from src.models.db.subscription import Subscription
from src.models.db.transaction import Transaction
from src.models.db.recurring_transaction import RecurringTransaction
from src.models.db.user_pref import UserPreference
from src.models.db.audit_log import AuditLog
from src.models.db.analytics_event import AnalyticsEvent
from src.models.db.terms_acceptance import TermsAcceptance
from src.models.db.streak import Streak

# Import User last so all other models are already defined
from src.models.db.user import User

__all__ = [
    "Currency",
    "Role",
    "Permission",
    "RolePermission",
    "OTP",
    "Account",
    "Category",
    "Budget",
    "Goal",
    "Subscription",
    "Transaction",
    "RecurringTransaction",
    "UserPreference",
    "AuditLog",
    "AnalyticsEvent",
    "TermsAcceptance",
    "Streak",
    "User",
]