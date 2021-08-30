#!/usr/bin/env python3
import numpy as np
from icalendar import Calendar, Event, vText, vCalAddress
import requests
from bs4 import BeautifulSoup
import re
import os
from src import Booking, Lesson_Report, Box_Manager, Helpful_Resources, Exam_Boards_Translate_Table


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
            booking = Booking.Booking(name, lesson, timing, confirmation)
            bookings_list.append(booking)
    return bookings_list


def generate_reports(bookings, path="Cookie.conf"):
    def generate_lesson_report(booking, messages, cookies):
        report = Lesson_Report.LessonReport(booking.ID)
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
                    start_time_UTC = Booking.standardise_timing(time, recurring=False)[0]
                    if start_time_UTC == booking["booking_start_datetime"]:
                        valid_chat_html = this_chat
                        break
            if valid_chat_html is not None:
                break
        if valid_chat_html is None:
            return None

        for message in valid_chat_html.find_all("div", {"class", "message sent"}):
            report_html = message.find("div", {"class","messagecard sent lessonreport"})
            if report_html is not None:  # It's a report
                time = message.find("header").getText().split("\n\n\t\t\t")[1].replace("\n\t\t", "")
                time_UTC = Booking.standardise_timing("DAY "+time, recurring=False, hour_correction=False)[0]
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


def generate_calendar_file(bookings_list, filename="My_Tutor_Calendar.ics", me=("Mateusz Ogrodnik", "mateusz.gardener@gmail.com")):
    cal = Calendar()
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')
    cal.add("X-WR-CALNAME", "MyTutor Calendar")
    cal.add("REFRESH-INTERVAL;VALUE=DURATION", "P30M")
    cal.add("color", "5")

    booking_ids = []
    for booking in bookings_list:
        if booking.ID not in booking_ids:
            description = f"""My Tutor Lesson
{booking['lesson_name']}
{booking['student_name']}

Progress: {booking.last_report['Progress']}
Good: {booking.last_report['Good']}
Improve: {booking.last_report['Improve']}
Next: {booking.last_report['Next']}

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

            organizer = vCalAddress(f'''MAILTO:{me[1]}''')
            organizer.params['cn'] = vText(f'''{me[0]}''')
            organizer.params['role'] = vText('CHAIR')
            event['organizer'] = organizer
            event['location'] = vText('MyTutor')

            attendee = vCalAddress('MAILTO:nomail@example.com')
            attendee.params['cn'] = vText(booking['student_name'])
            attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
            event.add('attendee', attendee, encode=0)

            if booking['status'] not in ["Confirmed", "Payment scheduled"]:
                event.add("STATUS", "TENTATIVE")
            else:
                event.add("STATUS", "CONFIRMED")
            cal.add_component(event)

    f = open(filename, 'wb')
    f.write(cal.to_ical())
    f.close()


def generate_helplinks(bookings_list: list):
    link_translation_table = Exam_Boards_Translate_Table.TransitionTable("src/Exam_Boards_Link_Table.csv")
    for i in range(len(bookings_list)):
        HR = Helpful_Resources.Help_Links(bookings_list[i], link_translation_table)
        bookings_list[i].help_links = HR.generate_helplinks()
    return bookings_list

script_dir = os.path.dirname(os.path.realpath(__file__))
cal_file = os.path.join(script_dir, "My_Tutor_Calendar.ics")
cookie_file = os.path.join(script_dir, "Cookie.conf")
json_file = os.path.join(script_dir, "config.json")
my_details = ("Mateusz Ogrodnik", "mateusz.gardener@gmail.com")

bookings_list = generate_booking_list(path=cookie_file)
bookings_list = generate_helplinks(bookings_list)
for booking in bookings_list:
    print(booking['lesson_name'], booking.help_links)
bookings_list = generate_reports(bookings_list, path=cookie_file)
generate_calendar_file(bookings_list, filename=cal_file, me=my_details)
man = Box_Manager.Box_Manager(file_path=cal_file, config=json_file)
res = man.update()

# gets the link for the calendar client
output_link = False
if output_link:
    print(res)
