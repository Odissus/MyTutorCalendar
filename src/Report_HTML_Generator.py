from typing import List, Dict
import re
import io
import Booking


class HTML_Report:
    Key_words = ["student_name", "lesson_name", "start_date", "start_time", "start_weekday", "booking_type", "Progress",
                 "Good", "Improve", "Next"]
    Report = ""
    loc = ""

    @staticmethod
    def initialise(report_loc: str):
        """
        Potentially deprecated

        :param report:
        :return:
        """
        with io.open(report_loc, "r", encoding="utf-8") as f:
            text = f.read()
            HTML_Report.Report = text
        HTML_Report.loc = report_loc

    @staticmethod
    def generate_report(booking: Booking):
        """
        Generates the html for a specific booking after initialisation

        :param booking:
        :return:
        """
        this_report = str(HTML_Report.Report) # creates a copy
        for word in HTML_Report.Key_words:
            this_report = re.sub(f'#{word}#', booking[word], this_report)
        return this_report