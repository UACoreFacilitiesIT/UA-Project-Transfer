# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2019/11/25 [1.0.1](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer)

Fixed some code that was confusingly copy-and-pasted, fixed a bug with the logging.

- Fixed project_lims_tools batch_post_containers bug where it may have been making far too many containers.

- Updated some code in that method to make a little more sense.

- Removed everything but warnings from project_lims_tools' logger calls.

- Now create_researcher always returns a uri.

#### 2019/11/20 [1.0.0](https://github.com/UACoreFacilitiesIT/UA-Project-Transfer/commit/42eb6b12149d3f11eb8fb19dcfda0d8553ceb021)

The first official UA-Project-Transfer release.
