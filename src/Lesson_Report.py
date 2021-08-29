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