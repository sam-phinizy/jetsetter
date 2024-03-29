import os

import nox


@nox.session
def lint(session):
    session.install("-r", "requirements-dev.lock")
    session.run("ruff", "format", ".")
    session.run("ruff", ".", "--fix")


@nox.session(python=["3.12"])
def tests(session):
    session.install("-r", "requirements-dev.lock")
    os.chdir("tests")
    session.run("pytest")


@nox.session
def typecheck(session):
    session.install("-r", "requirements-dev.lock")
    session.run("pyright", "src", external=True)
