"""Tests for the command-line interface."""

from __future__ import annotations

import pytest

from momentum_ultra import __version__
from momentum_ultra.cli import _build_parser, main


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --version displays the version string and exits with 0."""
    exit_code = main(["--version"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert __version__ in (captured.out + captured.err)


def test_main_no_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that running with no arguments prints help and exits with 0."""
    exit_code = main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "momentum-ultra" in captured.out


def test_dry_run_flag_parsing() -> None:
    """Test that dry-run is True by default and False with --no-dry-run."""
    parser = _build_parser()
    args_default = parser.parse_args([])
    assert args_default.dry_run is True

    args_no_dry_run = parser.parse_args(["--no-dry-run"])
    assert args_no_dry_run.dry_run is False

    args_dry_run = parser.parse_args(["--dry-run"])
    assert args_dry_run.dry_run is True
