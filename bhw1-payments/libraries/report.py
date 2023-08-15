import pandas as pd


class Report:
    def __init__(self):
        self.df = pd.DataFrame(
            columns=[
                "invoice_file",
                "failure_reason",
                "client_name",
                "service_date",
                "cpt_code",
                "expected_data",
                "actual_data",
            ]
        )

    def add_data(self, data):
        if not data:
            return

        for row in data:
            self.df = self.df.append(row, ignore_index=True)

    def create_report_file(self):
        print("\n\nREPORT:")
        print(self.df)
        self.df.to_csv("output/report.csv", index=False)
