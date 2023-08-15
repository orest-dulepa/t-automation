import pandas as pd
import numpy as np

from .exceptions import DuplicatedClient, MissingClient


class Clients(object):
    def __init__(self, path_to_file):
        self.df = pd.read_csv(path_to_file)
        self.df["FullName"] = self.df[["LastName", "FirstName"]].apply(
            lambda row: ", ".join(row.values.astype(str)), axis=1
        )
        self.df["duplicated_client_fullname"] = self.df.duplicated(subset=["FullName"])
        self.duplicated_client_fullnames = self.df.loc[
            self.df["duplicated_client_fullname"] == True, "FullName"
        ].tolist()

    def get_client_id(self, client_name):
        if client_name in self.duplicated_client_fullnames:
            raise DuplicatedClient()

        df_full_name = (
            self.df["FullName"]
            .str.replace(".", "", regex=False)
            .str.replace('"', "", regex=False)
            .str.upper()
        )
        df_last_name = (
            self.df["LastName"]
            .str.replace(".", "", regex=False)
            .str.replace('"', "", regex=False)
            .str.upper()
        )
        df_first_name = (
            self.df["FirstName"]
            .str.replace(".", "", regex=False)
            .str.replace('"', "", regex=False)
            .str.upper()
        )

        invoice_full_name = client_name.upper().strip()
        invoice_last_name, invoice_first_name = invoice_full_name.split(",")

        try:
            return self.df.loc[
                (
                    (df_full_name == invoice_full_name)
                    | (df_full_name == " ".join(invoice_full_name.split()[:2]))
                    | (
                        (df_last_name == invoice_last_name)
                        & (df_first_name.isin(invoice_first_name.split()))
                    )
                    | (
                        (df_last_name == invoice_last_name)
                        & (df_first_name.str.contains(invoice_first_name.split()[0]))
                    )
                    | (
                        (df_last_name.str.contains(invoice_last_name))
                        & (df_first_name.isin(invoice_first_name.split()))
                    )
                ),
                "Id",
            ].iloc[0]
        except IndexError:
            raise MissingClient()
