from queue import Queue
from typing import Any
from pathlib import Path
from threading import Event

from ..config.config import app_config
from ..utils.utils import connect_db

# --------------------------- Shared Variables --------------------------
DATABASE_CONFIG: dict[str, Any] = app_config["database_config"]
ROOT: Path = Path(app_config["global_config"]["root"])
BATCH_SIZE: int = app_config["global_config"]["batch_size"]
FETCH_QUERY: str = (
    """
    SELECT statement_id, date, narration, amount, direction, balance
    FROM statement_clean.transactions_clean
    """
)
