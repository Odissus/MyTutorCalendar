import pandas as pd


class CookieTableReader:
    data_frame = pd.DataFrame()

    @staticmethod
    def _set_csv_directory(csv_directory):
        CookieTableReader.data_frame = pd.read_csv(csv_directory)

    @staticmethod
    def get_cookies(csv_directory):
        """
        Table reader of the csv file holding cookies.
        name | cookie | email

        :param csv_directory: directory to the csv holding the cookie files
        """
        CookieTableReader._set_csv_directory(csv_directory)
        for i in CookieTableReader.data_frame.index:
            yield CookieTableReader.data_frame.iloc[i]
