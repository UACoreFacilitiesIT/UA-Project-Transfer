# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
