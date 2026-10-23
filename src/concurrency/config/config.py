import logging
from typing import cast 
from pathlib import Path

from omegaconf import OmegaConf
from dataclasses import dataclass, field

from .model import DatabaseModel, GlobalModel

logger = logging.getLogger(__name__)

REPO_ROOT: Path = Path(__file__).resolve().parents[3]

@dataclass
class Config:
    """Application configuration combining global settings and MySQL connection settings."""

    global_config: GlobalModel = field(
        metadata={
            "description": "The project root directory and database fetch batch size"
        }
    )
    database_config: DatabaseModel = field(
        metadata={
            "description": "The MySQL server connection and authentication settings"
        }
    )


def load_config():
    """Read, load, validate and store config file as a class object"""
    yaml_file_path: Path = Path(__file__).with_name("config.yaml")

    logger.info("Searching for configuration file")
    if not yaml_file_path.is_file():
        raise FileNotFoundError(
            f"YAML configuration not found at {yaml_file_path}"
        )

    logger.info("Loading configuration file")
    try:
        yaml_config = OmegaConf.load(yaml_file_path)

        # update configuration root value
        yaml_config.env.global_config.root = str(REPO_ROOT) 

        # validate and merge configuration    
        schema = OmegaConf.structured(Config)
        config = OmegaConf.merge(schema, yaml_config.env)

        # convert config to a python object and return it
        return cast(Config, OmegaConf.to_object(config))
    
    except Exception:
        logger.exception("Error loading configuraion file")
        raise

app_config: Config = load_config()