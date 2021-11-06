#!/usr/bin/env python3
from icalendar import Calendar, Event, vText, vCalAddress, Alarm
from src import *
from typing import List, Tuple
import hashlib


def generate_booking_list(prices_file_path: str) -> List[Booking]:
    bookings_list = MyTutorParser.generate_booking_list_from_bookings()
    # generate prices
    Pricer.set_path(prices_file_path)
    for i, booking in enumerate(bookings_list):
        bookings_list[i] = Pricer.price(booking)
    return bookings_list


def generate_reports(bookings: List[Booking]) -> List[Booking]:
    bookings = MyTutorParser.generate_reports(bookings)
    for booking in bookings:
        booking.last_report_HTML = HTML_Report.generate_report(booking)
    return bookings


def generate_calendar_file(bookings_list: List[Booking], filename: str, me: Tuple[str, str]) -> None:
    cal = Calendar()
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')
    cal.add("X-WR-CALNAME", "MyTutor Calendar")
    cal.add("REFRESH-INTERVAL;VALUE=DURATION", "P5M")
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

Price: {booking['price']}

Start <https://www.mytutor.co.uk/tutors/secure/bookings.html>
"""
            booking_ids.append(booking.ID)
            event = Event()
            event.add('summary', f"MyTutor - {booking['lesson_name']} - {booking['student_name']}")
            event.add('dtstart', booking["booking_start_datetime"])
            event.add('dtend', booking["booking_end_datetime"])
#            event.add("CATEGORIES", ["MyTutor"])
            event['uid'] = booking.ID
            event.add('priority', 5)
            event.add("DESCRIPTION", description)
            #event.add("X - ALT -DESC", f'FMTTYPE = text / html:{booking.last_report_HTML}')

            organizer = vCalAddress(f'''MAILTO:{me[1]}''')
            organizer.params['cn'] = vText(f'''{me[0]}''')
            organizer.params['role'] = vText('CHAIR')
            event['organizer'] = organizer
            event['location'] = vText('MyTutor')

            attendee = vCalAddress(f"MAILTO:{booking['student_name']}@odissus.com")
            attendee.params['cn'] = vText(booking['student_name'])
            attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
            event.add('attendee', attendee, encode=0)

            if booking['status'] in ["Confirmed", "Payment scheduled"]:
                event.add("STATUS", "CONFIRMED")
            elif booking['status'] in ["Matching Team"]:
                event.add("STATUS", "FREE")
            else:
                event.add("STATUS", "TENTATIVE")
            cal.add_component(event)

    f = open(filename, 'wb')
    f.write(cal.to_ical())
    f.close()


def generate_help_links(bookings_list: List[Booking], path: str) -> List[Booking]:
    link_translation_table = Exam_Boards_Translate_Table(path)
    for i in range(len(bookings_list)):
        hr = Helpful_Resources(bookings_list[i], link_translation_table)
        bookings_list[i].help_links = hr.generate_helplinks()
    return bookings_list


def compile_calendar(name: str, email: str, cookie: str, logging: bool, calendar_files_directory: str):
    my_details = (name, email)
    MyTutorParser.set_cookie(cookie)


    bookings_list = generate_booking_list(prices_file)
    bookings_list = generate_help_links(bookings_list, exam_table_file)
    bookings_list = generate_reports(bookings_list)
    MyTutorParser.get_price_data()

    calendar_basename = f"""{name.replace(" ", "_")}_{hashlib.sha256(cookie.encode('utf-8')).hexdigest()}.ics"""
    calendar_filename = os.path.join(calendar_files_directory, calendar_basename)
    generate_calendar_file(bookings_list, filename=calendar_filename, me=my_details)

    # confirm message
    confirm_mgs = f"Successfully modified {len(bookings_list)} events for {name} ({email})"

    # gets the link for the calendar client
    output_link = True
    if output_link:
        confirm_mgs += f"\nLink to the calendar file can be found under: {calendar_basename}"
    print(confirm_mgs)

    if logging:
        print(Logger(bookings_list, path_to_log_file=f"{name}.log").log_string)


script_dir = os.path.dirname(os.path.realpath(__file__))
settings = Config.get(os.path.join(script_dir, "Config.txt"))

exam_table_file = os.path.join(script_dir, "src", "Exam_Boards_Link_Table.csv")
html_report_file = os.path.join(script_dir, "html", "session_details_outlook.html")
cookies_csv_file = os.path.join(script_dir, "cookies", "Cookies.csv")
prices_file = os.path.join(script_dir, "src", "Price_Bands.csv")
calendar_files_directory = settings["calendar_files_directory"].replace("\n", "")

Cookies = Cookie_Reader.get_cookies(cookies_csv_file)
HTML_Report.initialise(html_report_file)

for c in Cookies:
    compile_calendar(c["Name"], c["Email"], c["Cookie"], c["Logging"], calendar_files_directory)
