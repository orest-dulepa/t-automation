# TA1 - Stripe Fee Journal Entry

### Installation

It requires Python v3.7.5+ to run.

Install the dependencies and run the python file.
```sh
cd ta1-stripe-fee-journal-entry
pip3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Execution

For local run you should have this variables available in your env:

- BOT_ENV ('local' for local execution)
- BITWARDEN_USERNAME (should be set for local execution)
- BITWARDEN_PASSWORD (should be set for local execution)

```sh
python task.py
```

via *rcc*:
```sh
rcc run
```

