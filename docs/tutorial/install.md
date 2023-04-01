(install)=

# Install

LaTeXBuddy is a Python package and thus can be installed with `pip`. However, it
is not published to PyPI, but rather to GitLab Package Registry. This is because
we do not want to publish our unfinished software just yet. You can expect
LaTeXBuddy to become available on PyPI with the release of v1.0.0 Alpha 1.

## Install from GitLab Package Registry

To install the package, execute the following command:

```sh
pip install latexbuddy --index-url https://gitlab.com/api/v4/projects/28436730/packages/pypi/simple
```

This will install the latest version of the package.

### Other versions

```{important}
GitLab Package Registry is mutable, which means we can delete packages if we
want to. For now, we are experimenting with publishing a lot, so we can't
guarantee that a particular version will never get deleted from the registry,
especially the pre-release versions.
```

To install other versions and to view the generic information about the package,
you can navigate to
[the package registry page](https://gitlab.com/LaTeXBuddy/LaTeXBuddy/-/packages).
