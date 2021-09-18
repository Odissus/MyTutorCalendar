from boxsdk import JWTAuth, Client
import os


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
        new_file = self.client.folder("0").upload(file_path)
        self.file_id = new_file.id

    def update(self):
        self.client.file(self.file_id).update_contents(self.file_path)
        url = self.client.file(self.file_id).get_shared_link(
            access='open', allow_download=True, allow_preview=True).split("/")[-1]
        download_url = f"https://app.box.com/index.php?rm=box_download_shared_file&shared_name={url}&file_id=f_{self.file_id}"
        return download_url