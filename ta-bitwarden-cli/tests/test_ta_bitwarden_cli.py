#!/usr/bin/env python

"""Tests for `ta_bitwarden_cli` package."""

import pytest
import os

from ta_bitwarden_cli import ta_bitwarden_cli as ta
from ta_bitwarden_cli import download_bitwarden as db


class TestSmoke:
    """
    For succesfull execution you need to have such env vars with valid values available in your system:
      - BITWADEN_USERNAME
      - BITWARDEN_PASSWORD
    """

    @classmethod
    def setup_class(self):
        db.DownloadBitwarden.download_bitwarden()

    def setup_method(self):
        bitwarden_credentials = {
            "username": os.getenv("BITWARDEN_USERNAME"),
            "password": os.getenv("BITWARDEN_PASSWORD"),
        }
        self.bw = ta.Bitwarden(bitwarden_credentials)

    def test_exe(self):
        app = self.bw.bitwarden_exe("logout")
        assert app.stderr == "You are not logged in."

    def test_login(self):
        self.bw.bitwarden_login()
        assert len(self.bw.bitwarden_token) > 80

    def test_get_data(self):
        creds = {
            "test": "pypi.org",
        }
        self.bw.bitwarden_login()
        self.bw.get_data(creds)
        assert self.bw.data["test"]["login"] == "ta"

    def test_get_credentials(self):
        creds = {
            "test": "pypi.org",
        }
        assert self.bw.get_credentials(creds)["test"]["login"] == "ta"
