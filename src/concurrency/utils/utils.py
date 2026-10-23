import sys
import logging
from typing import Any

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

logger = logging.getLogger(__name__)

def connect_db(config: dict[str, Any]) -> MySQLConnectionAbstract | PooledMySQLConnection:
    """connect to MySQL database"""
    try:
        database_connection = mysql.connector.connect(
            **config,
        )
        return database_connection
    except Exception:
        logger.exception("Database connection failed")
        sys.exit(1)