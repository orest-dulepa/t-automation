from RPA.Robocloud.Secrets import Secrets
from libraries import common as com
from libraries import bitwarden
from libraries.web_caseaware import CaseAware

ENV = ''
CREDS = {
    'caseaware': 'RSMA - Caseaware'
}

SAFE_NETS = True


def main():
    ENV = com.get_env()
    bot_creds = get_all_credentials(ENV)
    com.log_message('Start RSMA1 - BK Close Case Bot')
    com.print_version()
    ca_object = CaseAware(bot_creds['caseaware'], SAFE_NETS)

    com.log_message('Starting CaseAware', 'INFO')
    ca_object.open_login()
    ca_object.get_tasks()
    if ca_object.any_task:
        for case in ca_object.cases_to_process:
            ca_object.navigate_to_case(case['case_number'])
            if ca_object.is_task_completed():
                ca_object.navigate_to_fees()
                if ca_object.can_close_case:
                    ca_object.close_case()
                    com.log_message(case['case_number']+' Case Status in Case Aware is now "Closed"')
                else:
                    continue
            else:
                continue
    else:
        com.log_message(ca_object.error_message, 'ERROR')
        exit(1)
    ca_object.close_logout()

    com.log_message('100% task - Bot has completed its task', 'INFO')
    com.log_message('End RSMA1 - BK Close Case Bot')


def get_all_credentials(env: str, credentials_name: str = 'bitwarden_credentials'):
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)
    bw = bitwarden.Bitwarden(bitwarden_credentials)
    return bw.get_credentials(com.generate_creds(env, CREDS))


if __name__ == "__main__":
    main()
