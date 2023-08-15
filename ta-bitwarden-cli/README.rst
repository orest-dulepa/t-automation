================
ta-bitwarden-cli
================


.. image:: https://img.shields.io/pypi/v/ta_bitwarden_cli.svg
        :target: https://pypi.python.org/pypi/ta_bitwarden_cli

.. image:: https://img.shields.io/travis/macejiko/ta_bitwarden_cli.svg
        :target: https://travis-ci.com/macejiko/ta_bitwarden_cli

.. image:: https://readthedocs.org/projects/ta-bitwarden-cli/badge/?version=latest
        :target: https://ta-bitwarden-cli.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

|

TA BitWarden CLI installation package

|

Installation
------------

For correct work please use python virtualenv approach! 
Also use *--no-cache-dir* option.
Otherwise it would cache package wheel and wont download **bw** CLI binary anymore

::

   python3 -m virtualenv venv
   source venv/bin/activate
   pip install --no-cache-dir ta-bitwarden-cli 

Code above will additionally install **bw** CLI binary to a first available folder in the $PATH

|

Example Usage
-------------

.. code:: python

        import os
        from ta_bitwarden_cli import ta_bitwarden_cli as ta

        bitwarden_credentials = {
            "username": os.getenv("BITWARDEN_USERNAME"),
            "password": os.getenv("BITWARDEN_PASSWORD"),
        }
        creds = {
            "my_vault_item": "Google Maps API Key",
        }
        bw = ta.Bitwarden(bitwarden_credentials)
        assert bw.get_credentials(creds)["my_vault_item"]["password"] == "XXXXXXX"

|

Troubleshooting
---------------

If you use Windows during code execution you could face with something like:

::

   FileNotFoundError: [WinError 2] The system cannot find the file specified

This means that no binary is available. In that case please manually download BitWarden CLI binary from https://vault.bitwarden.com/download/?app=cli&platform=windows
and put it to any folder from $PATH. This approach is similar to chromedriver

|

Development
-----------

**Prepare local dev env:**

::

   python3 -m virtualenv venv
   source venv/bin/activate
   pip install -r requirements.txt

**Testing:**

::

   BITWARDEN_USERNAME=XXX BITWARDEN_PASSWORD=YYY pytest

**Pushing new package version:**

::

  bump2version minor
  git push origin YOUR_BRANCH



