from libraries import common as com
from libraries.process import ProcessExecutor


def main():
    try:
        com.log_message('Start Trumpet Behavioral Health 4 - Bumblebee')
        com.log_message('Version 1.2.5')
        process = ProcessExecutor()
        process.check_and_create_folders()


        com.log_message('5% field - Logging In')
        process.generate_list_of_clients()

        process.login_to_central_reach()
        process.set_filters()

        process.work_with_clients()

        process.get_and_read_contacts_file()
        process.generate_and_download_csv_files()

        process.generate_csv_report()

        com.log_message('100% task - Bot has completed its task', 'INFO')
        com.log_message('End Trumpet Behavioral Health 4 - Bumblebee')
    except Exception as ex:
        main_ex = Exception("Unexpected Error: " + str(ex))
        com.log_message(str(main_ex), "ERROR")


if __name__ == '__main__':
    main()
