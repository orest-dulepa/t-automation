import os
from libraries import common as com
from datetime import datetime

from config import BITWARDEN_DATA


def main():
    """
    Main function which calls all other functions.
    """
    date = str(datetime.today().strftime("%b-%d-%Y"))
    com.log_message("Start - TA1 - Stripe Fee Journal Entry")
    com.print_version()
    com.log_message(BITWARDEN_DATA["stripe"])

    com.log_message("100% task - Bot has completed its task", "INFO")
    com.log_message("End - TA1 - Stripe Fee Journal Entry")


if __name__ == "__main__":
    main()
