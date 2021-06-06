import numpy as np
from icalendar import Calendar, Event
from datetime import datetime, timedelta
from pytz import UTC
import requests
from bs4 import BeautifulSoup
import re
import calendar
from boxsdk import JWTAuth, Client
import os


def standardise_timing(time_string: str, recurring=True, hour_correction=True):
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
    booking__start_datetime = datetime(booking_year, month_no, day, hours - int(hour_correction), minutes, 0, 0, tzinfo=UTC)
    if recurrence == "Free meeting":
        booking__end_datetime = booking__start_datetime + timedelta(minutes=15)
    else:
        booking__end_datetime = booking__start_datetime + timedelta(hours=1)
    return booking__start_datetime, booking__end_datetime, recurrence


class LessonReport:
    def __init__(self, booking_id):
        self.key_names = ["Progress", "Good", "Improve", "Next"]
        self.data = {key: "" for key in self.key_names}
        self.icons = {f"{self.key_names[0]}_ico": "https://cdn.mytutor.co.uk/icons/emoji-write-pencil.png",
                      f"{self.key_names[1]}_ico": "https://cdn.mytutor.co.uk/icons/emoji-clapping-hands.png",
                      f"{self.key_names[2]}_ico": "https://cdn.mytutor.co.uk/icons/emoji-dartboard.png",
                      f"{self.key_names[3]}_ico": "https://cdn.mytutor.co.uk/icons/emoji-notes.png"}
        self.ID = booking_id

    def __getitem__(self, item):
        return {**self.data, **self.icons}[item]

    def __setitem__(self, key, value):
        self.data[key] = value


class Booking:
    def __init__(self, student_name: str, lesson_name: str, timing_data: str, status: str, price=0):
        self._student_name = student_name.replace("\n", "")
        self._lesson_name = lesson_name.replace("\n", "")
        self._booking_start_datetime, self._booking_end_datetime, self._recurrence = standardise_timing(
            timing_data.replace("\n", ""))
        self._price = price
        self._status = status
        self.last_report = None

    @property
    def _student_first_name(self):
        return self._student_name[:-3]

    @property
    def details(self):
        attr_names = [attr for attr in dir(self) if attr[0] == "_" and not attr[1] == "_"]
        dicc = {key[1:]: getattr(self, key) for key in attr_names}
        return dicc

    @property
    def ID(self):
        return self.__hash__()

    def __getitem__(self, item):
        return self.details[item]

    def __hash__(self):
        return hash(
            str(self["booking_start_datetime"]) + str(self["booking_end_datetime"]) + str(self["student_name"]))


class Box_Manager:
    def __init__(self, file_path="My_Tutor_Calendar.ics", config="config.json"):
        self.file_path = file_path
        self.filename = os.path.split(file_path)[1]
        self.client = Client(JWTAuth.from_settings_file(config))
        self.file_path = file_path
        for item in self.client.folder(folder_id="0").get_items():
            if item.name == self.filename:
                self.file_id = item.id
                return

    def update(self):
        self.client.file(self.file_id).update_contents(self.file_path)
        url = self.client.file(self.file_id).get_shared_link(
            access='open', allow_download=True, allow_preview=True).split("/")[-1]
        download_url = f"https://app.box.com/index.php?rm=box_download_shared_file&shared_name={url}&file_id=f_{self.file_id}"
        return download_url


def generate_booking_list(path="Cookie.conf"):
    with open(path, "r") as f:
        contents = f.read()
        cookie = contents.split(":")[1].strip()

    session = requests.Session()
    cookies = {"www.mytutor.co.uk": cookie}
    r = session.get("https://www.mytutor.co.uk/tutors/secure/bookings.html", cookies=cookies)
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
    return bookings_list


def generate_reports(bookings, path="Cookie.conf"):
    def generate_lesson_report(booking, messages, cookies):
        report = LessonReport(booking.ID)
        valid_chat_html = None
        latest_report = None
        for chat in messages:
            if booking["student_first_name"] in chat[0]:
                session = requests.Session()
                r = session.get(chat[1], cookies=cookies)
                this_chat = BeautifulSoup(r.text, "lxml")
                bookings_card = this_chat.find(id="tutorcardForm:bookingTiles")
                for lesson in bookings_card.find_all(id=re.compile("TUTORIAL\d{7}$")):
                    time = lesson.find("div", {"class", "booking-tile__time"}).getText().strip()
                    start_time_UTC = standardise_timing(time, recurring=False)[0]
                    if start_time_UTC == booking["booking_start_datetime"]:
                        valid_chat_html = this_chat
                        break
            if valid_chat_html is not None:
                break

        for message in valid_chat_html.find_all("div", {"class", "message sent"}):
            report_html = message.find("div", {"class","messagecard sent lessonreport"})
            if report_html is not None:  # It's a report
                time = message.find("header").getText().split("\n\n\t\t\t")[1].replace("\n\t\t", "")
                time_UTC = standardise_timing("DAY "+time, recurring=False, hour_correction=False)[0]
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


    with open(path, "r") as f:
        contents = f.read()
        cookie = contents.split(":")[1].strip()

    session = requests.Session()
    cookies = {"www.mytutor.co.uk": cookie}
    r = session.get("https://www.mytutor.co.uk/tutors/secure/messages.html", cookies=cookies)
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
        booking.last_report = generate_lesson_report(booking, chats, cookies)
    return bookings


def generate_calendar_file(bookings_list, filename="My_Tutor_Calendar.ics"):
    cal = Calendar()
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')
    cal.add("X-WR-CALNAME", "MyTutor Calendar")
    cal.add("REFRESH-INTERVAL;VALUE=DURATION", "P1H")
    cal.add("color", "5")

    booking_ids = []
    for booking in bookings_list:
        if booking.ID not in booking_ids:
            description = f"""
            My Tutor Lesson

            {booking['lesson_name']}
            {booking['student_name']}

            Current

            Previous

            Start <https://www.mytutor.co.uk/tutors/secure/bookings.html>
            """
            booking_ids.append(booking.ID)
            event = Event()
            event.add('summary', f"MyTutor - {booking['lesson_name']} - {booking['student_name']}")
            event.add('dtstart', booking["booking_start_datetime"])
            event.add('dtend', booking["booking_end_datetime"])
            event.add("CATEGORIES", ["MyTutor"])
            event['uid'] = booking.ID
            event.add('priority', 5)
            event.add("DESCRIPTION", description)
            if booking['status'] not in ["Confirmed", "Payment scheduled"]:
                event.add("STATUS", "TENTATIVE")
            else:
                event.add("STATUS", "CONFIRMED")
            cal.add_component(event)

    f = open(filename, 'wb')
    f.write(cal.to_ical())
    f.close()


script_dir = os.path.dirname(os.path.realpath(__file__))
cal_file = os.path.join(script_dir, "My_Tutor_Calendar.ics")
cookie_file = os.path.join(script_dir, "Cookie.conf")
json_file = os.path.join(script_dir, "config.json")

bookings_list = generate_booking_list(path=cookie_file)
generate_reports(bookings_list, path=cookie_file)
generate_calendar_file(bookings_list, filename=cal_file)
man = Box_Manager(file_path=cal_file, config=json_file)
res = man.update()
