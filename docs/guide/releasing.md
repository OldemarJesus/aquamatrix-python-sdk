# Release and Publishing

## GitHub Pages setup

The `documentation.yml` workflow builds MkDocs on pull requests and publishes the site on pushes to `main` or a manual workflow run. In the repository settings, set **Pages → Build and deployment → Source** to **GitHub Actions**. The public site URL is <https://oldemarjesus.github.io/aquamatrix-python-sdk/>.

## PyPI trusted publishing setup

Configure PyPI once before the first release:

1. Create the `aquamatrix-simar` project on PyPI, or open its **Publishing** settings if it already exists.
2. Add a pending trusted publisher with owner `OldemarJesus`, repository `aquamatrix-python-sdk`, workflow filename `publish.yml`, and environment name `pypi`.
3. In GitHub repository settings, create the `pypi` deployment environment. Optionally require approval for that environment.
4. Update `project.version` in `pyproject.toml`, run the checks, and commit the change.
5. Create a GitHub Release whose tag matches the version, for example `v0.1.0`. Publishing starts only after the release is published.

The workflow runs tests, lint, and type checks, builds wheel and source distributions, then publishes those exact artifacts using GitHub's OIDC identity. It does not need a PyPI API token or PyPI password stored in GitHub secrets.

Verify the version in `pyproject.toml` before each release; PyPI versions are immutable and cannot be overwritten. If a release fails, inspect the Actions run, correct the issue, and publish a new version rather than reusing an already published version.