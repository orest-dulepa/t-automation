from libraries import common, config
from libraries.enum.payors_group import PayorsGroup
from libraries.process.process_executor import ProcessExecutor

def main():
   common.print_version()
   process = ProcessExecutor()
   process.login_and_set_filters()

   process.payors_group_process(payors_group=PayorsGroup.COMMERCIAL)
   process.payors_group_process(payors_group=PayorsGroup.MEDICAID)

if __name__ == '__main__':
    main()
