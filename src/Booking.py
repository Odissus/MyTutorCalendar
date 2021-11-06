from datetime import datetime, timedelta
from pytz import UTC
import re
import calendar
import time


class Booking:
    def __init__(self, student_name: str, lesson_name: str, timing_data: str, status: str, price=0):
        self._student_name = student_name.replace("\n", "")
        self._parent_name = ""  # TODO add the parent's name, extracted from messages
        self._band = 1
        self._band_type = "Old"
        self._lesson_name = lesson_name.replace("\n", "")
        self._booking_start_datetime, self._booking_end_datetime, self._recurrence = self.standardise_timing(
            timing_data.replace("\n", ""))
        self._price = price
        self._status = status
        self.last_report = None
        self.last_report_HTML = None
        self.exam_board = None
        self.help_links = None
        self._start_date = "/".join(str(self._booking_start_datetime.date()).split("-")[::-1])
        self._start_weekday = calendar.day_name[self._booking_start_datetime.weekday()]
        self._start_time = str(self._booking_start_datetime.time())[:-3]  # no seconds
        self._booking_type = self.determine_booking_type()

        levels, self.level = ["A Level", "GCSE", "IB", "University"], "",
        for item in levels:
            if item in self._lesson_name:
                self.level = item
                break  # don't need to go through each level
        self.subject = str(self._lesson_name).replace(self.level, "").strip()

    def set_price_data(self, band_type: str, band: int):
        self._band_type, self._band = band_type, band

    def set_price(self, price):
        self._price = price

    @property
    def _student_first_name(self):
        return self._student_name[:-3]

    @property
    def details(self):
        attr_names = [attr for attr in dir(self) if attr[0] == "_" and not attr[1] == "_"]  # all protected attributes
        dicc = {key[1:]: getattr(self, key) for key in attr_names}
        if self.last_report is not None:  # extends this method to lesson report
            report_keys = self.last_report.key_names
            dicc.update({key[1:]: self.last_report[key] for key in report_keys})
        return dicc

    @property
    def ID(self):
        return self.__hash__()

    @property
    def price_band(self) -> tuple:
        return self._band_type, self._band, self.level

    def update_exam_board(self):
        exam_boards_list = ["AQA", "OCR", "Edexcel", "WJEC"]
        if self.last_report is not None:
            for item in exam_boards_list:
                if item in self.last_report["Progress"]:
                    self.exam_board = item

    def __getitem__(self, item):
        try:
            return self.details[item]
        except KeyError:  # from last report
            return self.last_report[item]

    def __setitem__(self, key, value):
        try:
            self.details[key] = value
        except KeyError:  # from last report
            self.last_report[key] = value

    def __hash__(self):
        return hash(
            str(self["booking_start_datetime"]) + str(self["booking_end_datetime"]) + str(self["student_name"]))

    def determine_booking_type(self):
        if self._booking_end_datetime - self._booking_start_datetime == 15:
            return "Free Meeting"
        return "Lesson"

    @staticmethod
    def standardise_timing(time_string: str, recurring=True):
        hour_correction = time.localtime().tm_isdst
        if "Today" in time_string:
            time_string = time_string[5:]
        else:
            time_string = time_string[3:]
        index = time_string.find(":") + 3
        recurrence = ""
        if recurring:
            recurrence = time_string[index:]
        time_det = time_string[:index]
        day = int(time_det.split(" ")[1])
        month = re.findall("[A-Z][a-z][a-z]", time_det)[0]
        booking_time = re.findall("\d+:\d\d", time_det)[0]

        month_cal = dict((v, k) for v, k in zip(calendar.month_abbr[1:], range(1, 13)))
        month_no = month_cal[month]
        hours, minutes = [int(t) for t in booking_time.split(":")]

        booking_year = datetime.now().year
        if datetime.now().month == 12 and month_no < 12:
            booking_year += 1

        # My Tutor is a bit backwards and can't handle timezones atm, hence hours-1 is currently in place
        booking__start_datetime = datetime(booking_year, month_no, day, hours - hour_correction, minutes, 0, 0,
                                           tzinfo=UTC)
        if recurrence == "Free meeting":
            booking__end_datetime = booking__start_datetime + timedelta(minutes=15)
        else:
            booking__end_datetime = booking__start_datetime + timedelta(hours=1)
        return booking__start_datetime, booking__end_datetime, recurrence