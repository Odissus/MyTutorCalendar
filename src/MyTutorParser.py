import requests
from bs4 import BeautifulSoup
import re
from src import Booking, Lesson_Report
from typing import List
import numpy as np


class MyTutorParser:
    session = requests.Session()
    cookies = {"www.mytutor.co.uk": ""}

    @staticmethod
    def set_cookie(cookie: str):
        MyTutorParser.session = requests.Session()  # reset session
        MyTutorParser.cookies = {"www.mytutor.co.uk": cookie}

    @staticmethod
    def generate_booking_list_from_bookings() -> List[Booking]:
        r = MyTutorParser.session.get("https://www.mytutor.co.uk/tutors/secure/bookings.html",
                                      cookies=MyTutorParser.cookies)
        soup = BeautifulSoup(r.text, "lxml")
        bookings_html = soup.find(id="upcomingSessions")

        bookings_list = []
        regex = re.compile(
            "classbookingform:classbookingtabs:upcomingSessionsGroupedByMomentList:\d+:upcomingSessionsDataTable_data")
        for section in bookings_html.find_all("tbody", {"id": regex}):
            for entry in bookings_html.find_all("tr", {"data-ri": re.compile("\d+")}):
                timing = entry.find("td", {"class", "tile__person tile__person--first"}) \
                    .find("p", {"class", "tile__meta tile--large"}).getText()
                details = entry.find_all("td", {"class", "tile__meta tile--large"})
                name = details[0].find("p").getText()
                lesson = details[1].getText()
                confirmation = entry.find_all("td", {"class", "tile--large"})[2].find("p").getText().strip()
                booking = Booking(name, lesson, timing, confirmation)
                bookings_list.append(booking)

        prices = MyTutorParser.get_price_data()
        if not prices.keys() == ["default"]:
            for booking in bookings_list:
                if booking['student_name'] in prices.keys():
                    price = prices[booking['student_name']]
                else:
                    price = prices["default"]
                band_type = ["New", "Old"][int("old" in price)]
                band = int(price[0])
                booking.set_price_data(band_type,band)
        else:
            [booking.set_price_data("New", int(prices["default"][0])) for booking in bookings_list]
        return bookings_list

    @staticmethod
    def generate_reports(bookings: List[Booking]):
        r = MyTutorParser.session.get("https://www.mytutor.co.uk/tutors/secure/messages.html",
                                      cookies=MyTutorParser.cookies)
        soup = BeautifulSoup(r.text, "lxml")
        messages_html = soup.find(id="chatsForCurrentUserForm:tutorMessagesTable_data")
        chats = np.array([["", ""]])
        for chat in messages_html.find_all("tr"):
            details = chat.find_all("td")[1]
            name = re.sub('\s+', ' ', details.find("p", {"class", "tile__name"}).getText())
            if "Parent" in name:
                name = name.split(" Parent of ")[1][:-1]
                link = f"https://www.mytutor.co.uk{details.find('div').get('onclick')[15:-1]}"

                while name in chats[:, 0]:  # God help why did you have to do this to me...
                    name += "x"
                chats = np.append(chats, [[name, link]], axis=0)
        chats = chats[1:]
        for booking in bookings:
            booking.last_report = MyTutorParser._generate_lesson_report(booking, chats)
        return bookings

    @staticmethod
    def _generate_lesson_report(booking: Booking, messages):
        report = Lesson_Report(booking.ID)
        valid_chat_html = None
        latest_report = None
        for chat in messages:
            if booking["student_first_name"] in chat[0]:
                r = MyTutorParser.session.get(chat[1], cookies=MyTutorParser.cookies)
                this_chat = BeautifulSoup(r.text, "lxml")
                bookings_card = this_chat.find(id="tutorcardForm:bookingTiles")
                for lesson in bookings_card.find_all(id=re.compile("TUTORIAL\d{7}$")):
                    time = lesson.find("div", {"class", "booking-tile__time"}).getText().strip()
                    start_time_UTC = Booking.standardise_timing(time, recurring=False)[0]
                    if start_time_UTC == booking["booking_start_datetime"]:
                        valid_chat_html = this_chat
                        break
            if valid_chat_html is not None:
                break
        if valid_chat_html is None:
            return report
        for message in valid_chat_html.find_all("div", {"class", "message sent"}):
            report_html = message.find("div", {"class", "messagecard sent lessonreport"})
            if report_html is not None:  # It's a report
                time = message.find("header").getText().split("\n\n\t\t\t")[1].replace("\n\t\t", "")
                time_UTC = Booking.standardise_timing("DAY " + time, recurring=False, hour_correction=False)[0]
                if latest_report is None:
                    latest_report = (report_html, time_UTC)
                elif latest_report[1] < time_UTC:  # This is a later report (more recent)
                    latest_report = (report_html, time_UTC)
        if latest_report is not None:
            chapter_slices = [17, 19, 22, 22]
            chapters = latest_report[0].find_all("li")
            report["Progress"] = chapters[0].getText()[chapter_slices[0]:]
            report["Good"] = chapters[1].getText()[chapter_slices[1]:]
            report["Improve"] = chapters[2].getText()[chapter_slices[2]:]
            report["Next"] = chapters[3].getText()[chapter_slices[3]:]
        return report

    @staticmethod
    def get_price_data():
        prices_data = {}
        r = MyTutorParser.session.get("https://www.mytutor.co.uk/tutors/secure/price-band.html",
                                      cookies=MyTutorParser.cookies)
        soup = BeautifulSoup(r.text, "lxml")
        sections = soup.find_all("div", {"class": "container__card__section"})
        default_band = sections[0].find_all("h3", {"class": "display--m u-margin-bottom--s"})[1].find("span").getText().strip()[5:]
        prices = sections[2].find(id="individualPriceBandsForm:priceBandsForParentTable_data").find_all("tr")
        if prices[0].find("td").getText() != "You have no individual prices set":
            for price in prices:
                items = price.find_all("td")
                parent = items[0].getText().strip()
                student = items[1].getText().strip()
                band = items[2].getText().replace("\n", "").strip().replace("\t", "")[5:]
                prices_data.update({student: band})
        prices_data.update({("default"): default_band})
        return prices_data

