from dataclasses import dataclass, field

@dataclass
class DatabaseModel:
    """Connection and authentication settings for the MySQL database."""
    
    host: str = field(
        metadata={
            "description": "The hostname or IP address of the MySQL server"
        }
    )
    port: int = field(
        metadata={
            "description": "The port number used to connect to the MySQL server"
        }
    )
    user: str = field(
        metadata={
            "description": "The username used to authenticate with the MySQL server"
        }
    )
    database: str = field(
        metadata={
            "description": "The name of the MySQL database to connect to"
        }
    )
    password: str = field(
        metadata={
            "description": "The password used to authenticate with the MySQL server"
        }
    )


@dataclass
class GlobalModel:
    """Project root directory and batch size used when exporting database rows."""

    root: str = field(
        metadata={
            "description": "The project root directory used to resolve data file paths"
        }
    )
    batch_size: int = field(
        default=1000, 
        metadata={"description": "The number of database rows to fetch per batch"}
    )
