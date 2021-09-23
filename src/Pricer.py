import pandas as pd
from collections import defaultdict
from src import Booking


class Pricer:
    _data = None

    @staticmethod
    def set_path(path_to_price_file: str):
        """
        Lookup object for searching for prices for bookings

        :param path_to_price_file: path to the csv file holding all the prices
        """
        df = pd.read_csv(path_to_price_file)
        Pricer._data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for row in df.itertuples():
            Pricer._data[row[1]][row[2]][row[3]].append(row[4:])

    @staticmethod
    def price(booking: Booking) -> Booking:
        """
        Works out the price for a given booking

        :param booking:
        :return:
        """
        price_type, price_band, level = booking.price_band
        booking_price = Pricer._data[price_type][price_band][level][0][0]
        if booking_price != "None":
            booking.set_price(booking_price)
        else:
            print(f"Price not found for booking {hash(booking)},{booking.details}")
        return booking
