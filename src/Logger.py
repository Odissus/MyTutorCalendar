from datetime import datetime


class Log:
    def __init__(self, bookings_list: list, path_to_log_file="log"):
        self.p2log, self.bookings_list = path_to_log_file, bookings_list
        self.log_string = f"""
        ########LOG START########
        {str(datetime.now())}
        Events written: {len(bookings_list)}
        Events hash:    {self.__calc_hash()}"""
        if len(bookings_list) > 0:
            self.log_string += f"""
        First event:
        {self._disp_event_details(bookings_list[0])}
        Last event:
        {self._disp_event_details(bookings_list[-1])}"""
        self.log_string += "#########LOG END#########"
        self._log()

    def _disp_event_details(self, event):
        my_str = ""
        dets = event.details
        for key in dets:
            my_str += f"    {key}:  {dets[key]}\n"
        return my_str

    def _log(self):
        with open(self.p2log, "a") as log_file:
            log_file.write(self.log_string.replace("        ", ""))

    def __calc_hash(self):
        return hash(sum([hash(booking) for booking in self.bookings_list]))
