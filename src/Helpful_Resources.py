class Help_Links:
    def __init__(self, booking, transition_table):
        self.syllabus, self.past_papers, self.PMT, self.TES, self.dates = None, None, None, None, None
        levels, level, subject = ["A Level", "GCSE", "IB", "University"], "", ""
        for item in levels:
            if item in booking['lesson_name']:
                level = item
                break  # don't need to go through each level
        subject = booking['lesson_name'].replace(level, "").strip()
        # TODO: Implement a way to get the exam board
        exam_board = "AQA"

        links = transition_table.get_data(exam_board, level, subject)
        if links is not None:
            self.syllabus, self.past_papers, self.dates = links

    def generate_helplinks(self):
        return {"syllabus": self.syllabus, "past_papers": self.past_papers,
                "PMT": self.PMT, "TES": self.TES, "dates": self.dates}
        # PMT
        # TES
        # key dates
