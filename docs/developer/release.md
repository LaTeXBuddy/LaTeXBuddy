# Releasing a new version

This section describes the process of releasing a new version of LaTeXBuddy. We
do not have a release schedule; the releases are usually published whenever we
want to. This may be changed later to a model where every push to `master`
publishes a new version.

:::{note}
LaTeXBuddy is not being published to PyPI as of now. The only way to get it is
from GitLab Package Registry. See :ref:`install docs<install>` for more
information.
:::

## Version numbering

The versioning of LaTeXBuddy adheres to the
[Semantic Versioning](https://semver.org/) (short: SemVer).

Each version number consists of three parts, which define the major, minor, and
patch version respectively. A valid version number would be, for example,
`1.2.3` or `0.23.2`. At the beginning of the development, the version number is
`0.0.0`, the first release then has the number `0.1.0`.

The patch version is to be incremented with each bugfix that does not break
compatibility with the previous release.

The minor version is to be incremented when new functions are added, that do not
break compatibility with the previous release.

The major version is to be incremented when new functions or bugfixes are
implemented, that break compatibility with the previous release (e.g. when
a file that could be read earlier can no longer be read).

Initially, the major version is equal to `0`; this means that the software
cannot yet be considered public, and _any_ increase in the minor or patch
version may (but shouldn’t) violate compatibility. With the first public
(‘Ready for Production’) release, the major version is increased to `1`.

## Requirements for a release

The releases are usually started by the maintainers. To kick off the initial
release discussion, one has to create a new branch off the `master` branch and
name it `release/<VERSION>`. For example: `release/0.5.0`. Then, a merge request
with the title "Draft: Prepare release <VERSION>" has to be created.

Upon creating the release, one has to do various checks before the merge request
can be un-drafted. This includes:

- running tests under every Python version (is usually done by the CI)
- compiling the CHANGELOG with Towncrier:

  ```sh
  towncrier build --version <VERSION> --yes
  ```

- checking newly documentation for correct rendering

After doing all that, the merge request can be un-drafted. It still has to get
a review of at least one maintainer before it can be merged.

## Releasing

Once the release is checked and everything seems fine, a maintainer can proceed
with the release:

1. Merge the request into the `master` branch
2. After the pipeline has completed, create a tag `v<VERSION>` on the latest
   commit
3. Wait for the release pipeline to publish the package and to create a new
   release
