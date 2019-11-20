# NOTE: Add environment specific methods here; if code exists, then that is
# what is necessary for project_transfer to run.

import os
import logging
import json
from ua_ilab_tools import ua_ilab_tools
from project_transfer import log_config_template, project_lims_tools


def setup_log():
    """Sets up the log for the entire module."""
    logging.config.dictConfig(log_config_template.CONFIG)


def setup_monitoring():
    """Sets up the monitoring software for the package (e.g. Sentry)."""
    pass


def setup_lims_api(env):
    """Initialize a LimsUtility object with a json creds file."""
    creds_path = (os.path.join(
        os.path.split(__file__)[0], "lims_token.json"))
    with open(creds_path, 'r') as file:
        creds = json.load(file)

    return project_lims_tools.LimsUtility(
        host=creds["host"],
        username=creds["username"],
        password=creds["password"])


def setup_ilab_api(env):
    """Initialize a IlabTools object with a json creds file."""
    creds_path = (os.path.join(
        os.path.split(__file__)[0], "ilab_token.json"))
    with open(creds_path, 'r') as file:
        creds = json.load(file)
    return ua_ilab_tools.IlabTools(creds["core_id"], creds["token"])
