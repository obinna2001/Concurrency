

class DatabaseConfig:
    host: str = ""
    port: int = 0
    user: str = ""
    database: str = ""
    password: str = ""


class GlobalConfig:
    batch_size: int = 100_000
    root: str = ""