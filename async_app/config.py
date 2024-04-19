import sys
import os
import json
import tomllib
from pathlib import Path

from platformdirs import site_config_dir, user_config_dir

from async_app.tools import app_name
from async_app.logger import logger


def read_config(config_name=None):
    if not config_name:
        config_name = app_name
    logger.debug(f"Using {config_name=}")

    config = {}
    logger.debug(f"Initial config: {json.dumps(config, indent=4)}.")

    site_config_path = Path(site_config_dir(config_name)) / "config.toml"
    logger.debug(f"Checking {site_config_path}.")
    if site_config_path.exists():
        with site_config_path.open("r") as fd:
            site_config = tomllib.loads(fd.read())
            config.update(site_config)
    logger.debug(f"Config after merging site config: {json.dumps(config, indent=4)}.")

    user_config_path = Path(user_config_dir(config_name)) / "config.toml"
    logger.debug(f"Checking {user_config_path}.")
    if user_config_path.exists():
        with user_config_path.open("r") as fd:
            user_config = tomllib.loads(fd.read())
            config.update(user_config)

    logger.debug(f"Config after merging user config: {json.dumps(config, indent=4)}.")

    logger.debug("Setting environment variables.")

    for key, value in config.items():
        env_key = f"{app_name}_{key}".upper()
        logger.debug(f"Setting {env_key} to {value}.")
        os.environ[env_key] = str(value)

    return config
