import pandas as pd
import numpy as np
from libraries import common as com
from datetime import datetime, date


class Invoice(object):
    def __init__(self, path_to_file):
        # This is ESCC's EOB's format
        try:
            self.invoice_type = "ESCC"
            self.df = pd.read_excel(path_to_file, header=7)
            self.df["Amount \nto Pay"] = (
                self.df["Amount \nto Pay"].str[1:].str.replace(",", "").astype(float)
            )
            raw_list = list(set(self.df["Client\nName"].tolist()))
            self.unique_client_names = [
                x for x in raw_list if str(x) != "nan" and str(x) != "Invoice Total:"
            ]
        # This is The BHPN EOB's format
        except KeyError:
            self.invoice_type = "BHPN"
            self.df = pd.read_excel(path_to_file, sheet_name="Charge Data")
            self.df["Charge Amount"] = self.df["Charge Amount"].astype(float)
            raw_list = list(
                set(
                    (
                        self.df["Client Last Name"]
                        + ", "
                        + self.df["Client First Name"]
                    ).tolist()
                )
            )
            self.unique_client_names = [x for x in raw_list if str(x) != "nan"]

        self.clients_data = {}
        self.get_clients_data()

    def get_clients_data(self):
        for client_name in self.unique_client_names:
            # This is ESCC's EOB's format
            try:
                self.clients_data[client_name] = self.df.loc[
                    self.df["Client\nName"] == client_name
                ]
            # This is The BHPN EOB's format
            except KeyError:
                last_name, first_name = client_name.split(",")
                self.clients_data[client_name] = self.df.loc[
                    (self.df["Client Last Name"] == last_name.strip())
                    & (self.df["Client First Name"] == first_name.strip()),
                ]

    def get_service_date(self, client_name):
        # This is ESCC's EOB's format
        try:
            return [
                datetime.strptime(d.split()[0], "%m/%d/%Y").strftime("%Y-%m-%d")
                for d in sorted(
                    self.clients_data[client_name]["Service\nDate"].tolist()
                )
            ]
        # This is The BHPN EOB's format
        except KeyError:
            return [
                d.date().strftime("%Y-%m-%d")
                for d in sorted(
                    self.clients_data[client_name]["Date of Service"].tolist()
                )
            ]

    def get_rows_number(self, client_name):
        return len(self.clients_data[client_name].index)

    def get_total_payment(self, client_name):
        # This is ESCC's EOB's format
        try:
            return round(self.clients_data[client_name]["Amount \nto Pay"].sum(), 2)
        # This is The BHPN EOB's format
        except KeyError:
            return round(self.clients_data[client_name]["Charge Amount"].sum(), 2)

    def get_apply_payment(self, client_name):
        # This is ESCC's EOB's format
        try:
            return [
                (
                    datetime.strptime(r["Service\nDate"].split()[0], "%m/%d/%Y"),
                    r["CPT\nCode"],
                    r["Amount \nto Pay"],
                )
                for r in self.clients_data[client_name].to_dict("records")
            ]

        # This is The BHPN EOB's format
        except KeyError:
            return [
                (
                    r["Date of Service"].date(),
                    r["Procedure Code"],
                    r["Charge Amount"],
                )
                for r in self.clients_data[client_name].to_dict("records")
            ]
