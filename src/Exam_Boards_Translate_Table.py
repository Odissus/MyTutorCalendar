import pandas as pd
from collections import defaultdict


class TransitionTable:
    def __init__(self, csv_directory):
        """
        Translation table for links to specific exam boards

        :param board: Exam Boards
        :param subject:
        :param level: A level, GCSE etc...
        """

        df = pd.read_csv(csv_directory)
        self._known_links = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for row in df.itertuples():
            self._known_links[row[1]][row[2]][row[3]].append(row[4:])

    def get_data(self, exam_board: str, level: str, subject: str):
        """
        Gets a Syllabus link,Past papers link, and key Dates link. Returns None if not in records

        :param exam_board:
        :param level:
        :param subject:
        :return:
        """
        links = self._known_links[exam_board][level][subject]
        if len(links) == 0:
            return None
        return tuple(links[0])

    def add_link(self):
        """
        Not implemented

        :return:
        """
        raise NotImplemented("Adding new links is not implemented yet")
