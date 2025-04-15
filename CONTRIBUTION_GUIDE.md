# Contributing to GAME SDK

There are various ways you can contribute to the GAME SDK, whether it's fixing bugs, adding new plugins, or improving the documentation.

### Submitting Code (e.g. plugins)
1. **Fork** the repository and clone it to your local machine.
2. **Create a Branch** for your changes.
3. **Make Changes** to address the issue or add the feature.
4. **Ensure Compliance** with the relevant contribution requirements:
    - For **general PRs**, follow the [default PR template](./.github/PULL_REQUEST_TEMPLATE/default.md).
    - For **plugin contributions**, ensure your PR follows the [plugin PR template](./.github/PULL_REQUEST_TEMPLATE/plugin.md).
5. **Commit** with a message that clearly explains your change.
6. **Push** the branch to your fork and submit a pull request.
7. **Label** the pull request appropriately based on the [label definitions](#label-definitions).

### General Contribution Guidelines
If you are contributing to the core SDK, ensure the following:
- The code is well-documented.
- Your PR follows the [default PR template](./.github/PULL_REQUEST_TEMPLATE/default.md).
- Screenshots, video demonstrations, or logs showcasing the changes are included (if applicable).

### Plugin Contribution Guidelines
If you are adding a new plugin, ensure the following:
- A `README.md` file exists in the plugin root directory and includes:
    - Installation instructions
    - Usage examples with code snippets
    - List of features and capabilities
    - Troubleshooting guide (if applicable)
    - Contribution guidelines (if applicable)
- A `plugin_metadata.yml` file exists in the plugin root directory with complete metadata as per the [plugin metadata template](./plugins/plugin_metadata_template.yml).
- Your PR follows the [plugin PR template](./.github/PULL_REQUEST_TEMPLATE/plugin.md).
- Screenshots, video demonstrations, or logs showcasing the plugin functionality are included (if applicable).

### Reporting Bugs
- Open an issue in the [Issues](https://github.com/game-by-virtuals/game-python/issues) tab and tag it as a `bug`.

### Suggesting Enhancements
- Open an issue in the [Issues](https://github.com/game-by-virtuals/game-python/issues) tab and tag it as an `enhancement`.

## Label Definitions
Please tag issues and pull requests appropriately, based on the definition below:
- **plugin**: A plugin contribution.
- **bug**: A problem that needs fixing.
- **enhancement**: A requested enhancement.
- **help wanted**: A task that is open for anyone to work on.
- **documentation**: Documentation changes.
