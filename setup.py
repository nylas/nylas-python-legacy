import sys
import re
import subprocess
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


VERSION = ""
with open("nylas_legacy/_client_sdk_version.py", "r") as fd:
    VERSION = re.search(
        r'^__VERSION__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

RUN_DEPENDENCIES = [
    "requests[security]>=2.4.2",
    "six>=1.4.1",
    "urlobject",
    "enum34>=1.1.10; python_version<='3.4'",
    "websocket-client==0.59.0",
]

TEST_DEPENDENCIES = [
    "pytest",
    "pytest-cov",
    "pytest-timeout",
    "pytest-mock",
    "responses==0.10.5",
    "twine",
    "pytz",
    "mock; python_version<'3.3'",
]

RELEASE_DEPENDENCIES = ["bumpversion>=0.5.0", "twine>=3.4.2"]


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        # pylint: disable=attribute-defined-outside-init
        self.pytest_args = [
            "--cov",
            "--cov-report=xml",
            "--junitxml",
            "./tests/output",
            "tests/",
        ]
        self.lint = False

    def finalize_options(self):
        TestCommand.finalize_options(self)
        # pylint: disable=attribute-defined-outside-init
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def main():
    # A few handy release helpers.
    # For publishing you should install the extra 'release' dependencies
    # by running: pip install nylas-legacy['release']
    if len(sys.argv) > 1:
        if sys.argv[1] == "publish":
            try:
                subprocess.check_output(["git", "push", "--follow-tags"])
                subprocess.check_output(["python", "setup.py", "sdist"])
                subprocess.check_output(["twine", "upload", "-r", "testpypi", "dist/*"])
                subprocess.check_output(["twine", "upload", "dist/*"])
            except FileNotFoundError as e:
                print("Error encountered: {}.\n\n".format(e))
            sys.exit()
        elif sys.argv[1] == "release":
            if len(sys.argv) < 3:
                type_ = "patch"
            else:
                type_ = sys.argv[2]
            try:
                subprocess.check_output(
                    ["bumpversion", "--current-version", VERSION, type_]
                )
            except FileNotFoundError as e:
                print(
                    "Error encountered: {}.\n\n".format(e),
                    "Did you install the extra 'release' dependencies? (pip install nylas-legacy['release'])",
                )
            sys.exit()

    setup(
        name="nylas-legacy",
        version=VERSION,
        packages=find_packages(),
        install_requires=RUN_DEPENDENCIES,
        dependency_links=[],
        tests_require=TEST_DEPENDENCIES,
        extras_require={"test": TEST_DEPENDENCIES, "release": RELEASE_DEPENDENCIES},
        cmdclass={"test": PyTest},
        author="Nylas Team",
        author_email="support@nylas.com",
        description="Python bindings for the Nylas API v2 (legacy).",
        license="MIT",
        keywords="inbox app appserver email nylas contacts calendar",
        url="https://github.com/nylas/nylas-python-legacy",
        long_description_content_type="text/markdown",
        long_description="""
# Nylas API v2 (Legacy) Python bindings

Python bindings for the Nylas API v2.

The Nylas APIs power applications with email, calendar, and contacts CRUD and bi-directional sync from any inbox in the world.

Nylas is compatible with 100% of email service providers, so you only have to integrate once.
No more headaches building unique integrations against archaic and outdated IMAP and SMTP protocols.""",
    )


if __name__ == "__main__":
    main()
