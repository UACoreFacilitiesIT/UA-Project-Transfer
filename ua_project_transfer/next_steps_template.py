"""Defines workflow routing methods, to be used by route_strategy."""
# NOTE: Change these functions to perform custom routing to your workflows and
# steps in your environment. WF_STEPS must also be updated. Be sure to include
# a logger defined in the log_config file to log anything within next_steps.

import logging

# Set up in log_config.
LOGGER = logging.getLogger("project_transfer.next_steps")


def specific_workflow(payload):
    """Evaluates values in the payload to selectively route samples."""
    pass


"""
For example:
from project_transfer.wf_steps import WF_STEPS
def agena(payload):
    if payload["form"].field_to_values[
            "Sample_Type_each_sample"] == "cells":
        payload["lims_api"].tools.step_router(
            *WF_STEPS[payload["env"]]["agena"]["cells"],
            payload["art_uris"])
    else:
        payload["lims_api"].tools.step_router(
            *WF_STEPS[payload["env"]]["agena"]["gdna"],
            payload["art_uris"])
"""
