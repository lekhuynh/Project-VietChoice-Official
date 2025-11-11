from ..database import Base  # re-export for convenience

# Import models to register with SQLAlchemy metadata (create_all)
from . import (
    users,  # noqa: F401
    categories,  # noqa: F401
    products,  # noqa: F401
    search_history,  # noqa: F401
    search_history_products,  # noqa: F401
    favorites,  # noqa: F401
    user_reviews,  # noqa: F401
)

__all__ = [
    "Base",
]
