"""Run available CI/CD tests, style check and typechecks using Nox."""

import nox

python = "3.8", "3.9", "3.10.4"
locations = "src", "tests", "noxfile.py"
nox.options.sessions = "lint", "type", "test"


@nox.session(python=python)
def lint(session):
    """Check the codebase against the Flake8 Google-style guide."""
    args = session.posargs or locations
    session.run("poetry", "install", external=True)
    session.run("flake8", *args)


@nox.session(python=python)
def type(session):
    """Typecheck the codebase using MyPy."""
    args = session.posargs or locations
    session.run("poetry", "install", external=True)
    session.run("mypy", *args)


@nox.session(python=python)
def test(session):
    """Run the test suite for code coverage."""
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.run("pytest", *args)
