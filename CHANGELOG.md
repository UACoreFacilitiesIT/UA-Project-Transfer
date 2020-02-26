# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2020/2/26 [1.1.6](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Small fix to updatng the logging config for emails.

- The logging config was never being updated due to silently catching errors. The function has been updated to actually update the logging config.

#### 2020/2/20 [1.1.5](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Small error checking fix related to UA-Ilab-Tools v2.0.2 changes.

- "harvest_form" now checks both if the current_form name is a skippable form, and skips that form, as well as check if the returned form has no samples. Previously this was done by UA-Ilab-Tools, but that has been changed with version 2.0.2.

#### 2020/2/19 [1.1.4](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Small bug fix pertaining to variable initialization.

- A previous release caused refactoring of code, which made moved the con_uri_name dictionary from use only internally to being used by check_samples as well. In the case where the Clarity project had no samples, this dictionary was never initialized, causing an error.

#### 2020/2/18 [1.1.3](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Updated from skipping forms with "Request a Quote" in their name to forms with "NQ" in their name.

#### 2020/2/17 [1.1.2](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Bug fix related to changed Clarity project names.

- If project names were changed in Clarity, project_trasnfer would not see that project as already having been moved, and this has been fixed by not querying Clarity projects for iLab request ids.

#### 2020/2/17 [1.1.1](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Added new error checks and logging calls and updated what samples get moved to Clarity.

- Added error checks for errors that stop program execution so following projects can be transferred.

- Will only move samples from iLab to Clarity if the container a sample belongs to is not already in Clarity.

- Added new logging calls which function as detailed information of program execution, and removed those related to the success of project transfers.

#### 2020/2/5/ [1.1.0](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Added more logging calls to provide more detailed information on a transfer's status.

- Added separate calls for both new project transfers and new sample transfers.

- Made more detailed calls when errors arise during transfers.

#### 2019/12/5 [1.0.3](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Small bug fixes related to file writing and reading.

- Fixed issue with error messages being written to file with double quotes forcing parent string to use single quotes, adding escape characters to other single quotes.

- Refactored gathering of project uris that do not need to be transfered.

- Added try/except catch around a delete operation that would previously halt execution when an error was raised.

#### 2019/12/3 [1.0.2](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Moved environment specific information to a template file, other small improvements.

- Added workflow locations dictionary that needs to be filled out by a user to core_specifics_template.py.

- Added unroutable_forms list that needs to be filled out by a user to core_specifics_template.py.

- Removed those two from project_lims_tools.py.

- Updated documentation of batch_post_samples in project_lims_tools to reflect its actual implementation.

- Removed uneccesary imports from project_transfer.py.

- Changed the loop over which files are opened from always starting at 2018 to finding the file with the smallest year and using that as its starting point.

- Updated tests to reflect new design decisions made since previous release.

#### 2019/11/25 [1.0.1](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Fixed some code that was confusingly copy-and-pasted, fixed a bug with the logging.

- Fixed project_lims_tools batch_post_containers bug where it may have been making far too many containers.

- Updated some code in that method to make a little more sense.

- Removed everything but warnings from project_lims_tools' logger calls.

- Now create_researcher always returns a uri.

#### 2019/11/20 [1.0.0](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer/commit/42eb6b12149d3f11eb8fb19dcfda0d8553ceb021)

The first official UA-Project-Transfer release.
