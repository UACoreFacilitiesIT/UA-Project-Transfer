"""Converts unprocessed ilab requests to Clarity projects."""
import argparse
import logging
import traceback
import datetime
import re
from dataclasses import dataclass, field
from ua_ilab_tools import ua_ilab_tools
from ua_project_transfer import project_lims_tools
from ua_project_transfer import core_specifics
from ua_project_transfer import price_check


# Set up log.
LOGGER = logging.getLogger(__name__)
core_specifics.setup_log()

# Set up script monitoring to be notified if it unexpectedly breaks.
core_specifics.setup_monitoring()


@dataclass
class ProjectRecord():
    """Holds the information required to log a project."""
    uri: str
    expected_price: str = ""
    actual_price: str = ""
    date: datetime.datetime = field(default_factory=datetime.datetime.now)


def get_project_history(log_file_name):
    """Harvest all of the uri's from the given log.

        Arguments:
            log_file_name (string): The path to the log file. If the file is
                in cwd, then it can be just the file name.

        Returns:
            processed_projects (set): The dict that holds all of the uri's
                that the script should skip (either they have been processed
                or an hour hasn't elapsed between the last failure).
    """
    processed_projects = set()
    error_entries = dict()
    error_projects = dict()
    with open(log_file_name, 'r') as file:
        for line in file.readlines():
            if "INFO" not in line and "ERROR" not in line:
                continue

            current_uri = line.split("uri=")[1].split()[0].strip("',")
            current_uri = re.sub(r"[^0-9]", '', current_uri)
            if "INFO" in line:
                # The project has been successfully transferred.
                processed_projects.add(current_uri)
            else:
                attempt_time = line.split("datetime(")[1].split("))")[0]
                attempt_datetime = datetime.datetime.strptime(
                    attempt_time, "%Y, %m, %d, %H, %M, %S, %f")
                error_entries[attempt_datetime] = current_uri

    # For all of the 'ERROR' entries, find the newest versions for every
    # unique uri.
    for entry_datetime, uri in error_entries.items():
        if uri in error_projects.values():
            for project_datetime, project_uri in error_projects.items():
                if uri == project_uri:
                    if project_datetime < entry_datetime:
                        del error_projects[project_datetime]
                        error_projects[entry_datetime] = uri
                        break
        else:
            error_projects[entry_datetime] = uri

    # Find out if an email and log record should happen.
    for project_datetime, project_uri in error_projects.items():
        if (datetime.datetime.now() - project_datetime
                < datetime.timedelta(hours=1)):
            # The project has failed, but it failed too recently
            # to try again.
            processed_projects.add(project_uri)

    return processed_projects


def main():
    # Set up the arguments with names for the different environments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ilab", dest="ilab_env", required=True)
    parser.add_argument(
        "--lims", dest="lims_env", required=True)
    args = parser.parse_args()

    lims_utility = core_specifics.setup_lims_api(args.lims_env)
    ilab_tools = core_specifics.setup_ilab_api(args.ilab_env)

    # Setup the charge pricing scheme.
    charge_per_reaction = {
        "Transgenic Mouse Genotyping": [
            "TGM Assay List",
            "TGM Other Assay List"],
        "Low Volume Sequencing": ["Primer"]}

    try:
        all_req_ids = ilab_tools.get_service_requests(status="processing")
    except RuntimeError:
        # No Requests to process.
        all_req_ids = {}

    # To process the entire history, regardless of the year in the file name.
    to_process = all_req_ids.keys()
    for year in range(2018, datetime.datetime.today().year + 1):
        current_log_name = f"project_transfer_log_{year}.txt"
        to_process = set(
            to_process).difference(get_project_history(current_log_name))

    for req_id in to_process:
        req_soup = all_req_ids[req_id]
        request_type = req_soup.find("category-name").string
        # If a log_config has initialized these handlers, reset the toaddrs of
        # those handlers. If there are not handlers with those names or that
        # attribute, pass.
        try:
            warn_index = LOGGER.handlers.index("warn_handler")
            error_index = LOGGER.handlers.index("error_handler")
            LOGGER.handlers[warn_index].toaddrs = core_specifics.get_email(
                request_type)
            LOGGER.handlers[error_index].toaddrs = core_specifics.get_email(
                request_type)
        except (ValueError, AttributeError):
            pass

        prj_info = ua_ilab_tools.extract_project_info(req_soup)
        current_record = ProjectRecord(uri=prj_info.name)
        try:
            forms_uri_to_soup = ilab_tools.get_custom_forms(req_id)

        except ua_ilab_tools.IlabConfigError:
            # Requests without forms are Consultation Requests or Custom
            # Projects that have not yet had a business form attached, and
            # so the request should just be skipped.
            continue
        # Make sure the current_form is zeroed out between request id's.
        else:
            current_form = None

        # Get all of the custom forms for the current req_id.
        for form_uri, form_soup in forms_uri_to_soup.items():
            # Get the form info (including the sample info) before you post
            # anything, as this is where most of the errors are thrown.
            try:
                current_form = ua_ilab_tools.extract_custom_form_info(
                    req_id, form_uri, form_soup)

            except TypeError as grid_error:
                LOGGER.error({
                    "template": "error.html",
                    "content": (
                        f"The request {current_record} has been filled out"
                        f" incorrectly. The error message is:\n {grid_error}")
                })
                break

            # Add the request_type to the form that was just added.
            current_form.request_type = request_type

            # If the request only has a 'Request a Quote' form, continue.
            if "REQUEST A QUOTE" in current_form.name.strip().upper():
                current_form = None
                continue

        # If there was an error with the business form, don't try to post info
        # that is not there.
        if current_form is None:
            continue

        # Try to post every part of a request, but if it fails, delete what was
        # made.
        delete_list = list()
        try:
            res_uri = lims_utility.create_researcher(req_id, prj_info)
            delete_list.append(res_uri)

            prj_uri = lims_utility.create_project(req_id, prj_info)
            delete_list.append(prj_uri)

            con_uris = lims_utility.create_containers(
                req_id, prj_info, current_form)
            delete_list.extend(con_uris)

            sample_uris = lims_utility.create_samples(
                req_id, prj_info, current_form)
            delete_list.extend(sample_uris)
        except project_lims_tools.POSTException:
            # Delete in reverse order, so Clarity allows you to delete things.
            for item in delete_list[::-1]:
                lims_utility.lims_api.tools.api.delete(item)
            break

        # Collect and compare the expected and actual prices.
        try:
            if request_type in charge_per_reaction.keys():
                req_price, calculated_price = price_check.check_request(
                    ilab_tools,
                    req_id,
                    request_type,
                    current_form.samples,
                    rxn_multiplier=charge_per_reaction[request_type])
            else:
                req_price, calculated_price = price_check.check_request(
                    ilab_tools,
                    req_id,
                    request_type,
                    current_form.samples)

            current_record.actual_price = req_price
            current_record.expected_price = calculated_price

        # Catch BaseException here because I don't want the program to ever
        # stop here if price_check throws an error.
        except BaseException:
            LOGGER.warning({
                "template": "price_warning.html",
                "content": (
                    f"The project {req_id} prices could not be checked. The"
                    f" traceback is:\n{traceback.format_exc()}")
            })

        sample_art_uris = lims_utility.lims_api.tools.get_arts_from_samples(
            sample_uris)
        # Assign those samples to workflows.
        try:
            lims_utility.route_strategy(
                sample_art_uris.values(), current_form, args.lims_env)

        # Catch BaseException here because I don't want the program to ever
        # stop here if route_strategy throws an error.
        except BaseException:
            LOGGER.warning({
                "template": "route_warning.html",
                "content": (
                    f"The project {req_id} could not be routed. The traceback"
                    f" is:\n{traceback.format_exc()}")
            })

        LOGGER.info(current_record)


if __name__ == '__main__':
    main()
