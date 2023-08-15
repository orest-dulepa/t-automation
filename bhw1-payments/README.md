# BHW-1 Payments

> Behavioral Healthworks Payments Bot

> Apply payments for all clients from Invoice files via Central Reach

## Workflow

- Download file with clients info from Central Reach
- Download all Invoice files from Google Drive for particular **CHECK_NUMBER** (i.e. GDrive folder name)
- For each unique client from each Invoice file do Bulk Apply Payment in Central Reach using **CHECK_DATE**
- Save to report file error info if it occurs
- Send report file to client's email via Google Mail

## Installation

It requires Python v3.7.5+ to run.

Install the dependencies and run the python file.
```sh
cd bhw1-payments
pip3 -m virtualenv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```

## Execution

Bot execution is configurable via this env vars:

- INVOICE_FILE (Process only this invoice file. Default is *None* (will proccess all files in the check number folder))
- BITWARDEN_ENV (*'local'* or *'robocloud'*. Get bitwarden creds from env vars or from Robocloud Vault. Default is 'local')
- BITWARDEN_USERNAME (should be set for local execution if *BITWARDEN_ENV=='local'*)
- BITWARDEN_PASSWORD (should be set for local execution if *BITWARDEN_ENV=='local'*)
- EXECUTION_ENV (*'local'* or *'ta'*. Where to get user input from. Default is *'local'*)
- CHECK_NUMBER (should be set for local execution if *EXECUTION_ENV=='local'*. Otherwise bot takes data from TA platform)
- CHECK_DATE (should be set for local execution if *EXECUTION_ENV=='local'*. Otherwise bot takes data from TA platform)
- EMAIL_RECIPIENT (where to send report after bot execution)
- BOT_MODE (*'apply'* or *'cancel'*. What button will bot click as final step. Default is *'cancel'*. Useful for dry runs)

example:
```sh
# bot execution in production
BITWARDEN_ENV=robocloud EXECUTION_ENV=ta BOT_MODE=apply python task.py
```

via *rcc*:
```sh
rcc run
```

