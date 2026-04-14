from invoke import task, Collection
import os
import subprocess
import sys
from logger import logger


"""
Invoke Tasks specification

inv --list      # list available tasks
inv dev     # run development server
inv test    # run tests
inv lint    # run linter


NOTE: All the commands is used with `poetry run`
EXAMPLE: `poetry run inv dev`
"""


@task
def dev(ctx):
    """Start the development server"""
    try:
        ctx.run(
            "uvicorn src.ai_local_daemon.main:app --uds /run/user/$(id -u)/ai_local_daemon/app.sock",
            pty=True,
            echo=True,
        )
    except Exception:
        logger.error("Failed to start development server", exc_info=True)
        sys.exit(1)


@task
def test(ctx):
    """Run tests"""
    try:
        ctx.run("pytest . -vv", pty=True, echo=True)
    except Exception:
        logger.error("Tests failed", exc_info=True)
        sys.exit(1)


@task
def lint(ctx):
    """Run ruff linter with auto-fix"""
    try:
        ctx.run("ruff check --fix .", pty=True, echo=True)
        result = ctx.run("ruff check .", pty=True, echo=True, warn=True)
        if result.exited != 0:
            logger.warning("Lint issues remain after auto-fix")
            sys.exit(1)
    except Exception:
        logger.error("Linting failed", exc_info=True)
        sys.exit(1)


@task
def format(ctx):
    """Format code with ruff"""
    try:
        ctx.run("ruff format .", pty=True, echo=True)
    except Exception:
        logger.error("Formatting failed", exc_info=True)
        sys.exit(1)


@task
def check(ctx):
    """Run full check before committing"""
    try:
        ctx.run("ruff check .", pty=True, echo=True)
        ctx.run("ruff format --check .", pty=True, echo=True)
        logger.info("✅ All checks passed!")
    except Exception:
        logger.error("Checks failed", exc_info=True)
        sys.exit(1)


# ====================== COLLECTIONS ======================

ns = Collection()

dev_ns = Collection("dev")
dev_ns.add_task(dev, name="server")
dev_ns.add_task(lint, name="lint")
dev_ns.add_task(format, name="format")
dev_ns.add_task(check, name="check")

ns.add_task(test)
ns.add_collection(dev_ns)
ns.default = "dev.server"   # running just `inv` will start the dev server

__all__ = ["ns"]
