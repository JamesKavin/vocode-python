# Contributing to Vocode

Hi there! Thank you for wanting to contribute to Vocode! We're an open source project and are extremely open to contributions like new features,integrations, or documentation.

To contribute, please ["fork and pull request"](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).

This project uses [Poetry](https://python-poetry.org/) as a dependency manager. Check out Poetry's [documentation on how to install it](https://python-poetry.org/docs/#installation) on your system before proceeding.

To install requirements:

```bash
poetry install
```

## 🗺️Contributing Guidelines

### 🚩GitHub Issues

Our [issues](https://github.com/vocodedev/vocode-python/issues) page has all of the bugs and enhancements that we want to implement. We have labels that split them into the following categories:

- enhancements: improvements to existing features or altogether new features
- bugs: identified issues that need fixing

If you are working on an issue, please assign to yourself! And please keep issues as modular/focused as possible.

We've marked the issues that we would love folks to work on first with 'good first issue' - see [here](https://github.com/vocodedev/vocode-python/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) for all such issues.

### 🙋Getting Help

We are in the process of making it as easy as possible to contribute but we completely understand if you run into issues.

Please contact us if you need help! We'd love to help + improve the process so that others don't run into similar issues. Come find us on [Discord](https://discord.gg/NaU4mMgcnC)!

We're working on our linting/documentation standards – and will have updates soon. We don't want that to get in your way at all.

### 🏭Release process

We release updates to Vocode on a daily basis published to [PyPI](https://pypi.org/project/vocode/).

If you submit a PR, we'd love to feature your contribution on Twitter so please include your handle in your PR/otherwise!

## Linting

We use [`black`](https://black.readthedocs.io/en/stable/) for linting. If you're using VSCode, code should auto-format automaticaly. Otherwise, run the following script before pushing:

```
make lint_diff
```

## Testing

🚧 Under construction

## Documentation

Our docs are currently [here](https://github.com/vocodedev/docs). If you make a change or notice that something is incorrect, please feel free to submit an update!
