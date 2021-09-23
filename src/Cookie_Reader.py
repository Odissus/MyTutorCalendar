import pandas as pd


class CookieTableReader:
    def __init__(self, csv_directory):
        """
        Table reader of the csv file holding cookies.
        name | cookie | email

        :param csv_directory: directory to the csv holding the cookie files
        """

        self.df = pd.read_csv(csv_directory)

    def get(self):
        for i in self.df.index:
            yield self.df.iloc[i]
