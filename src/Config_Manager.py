import os
from typing import Dict


class Config:
    path = ""
    settings = {}

    @staticmethod
    def _set_path(path: str):
        """
        Sets path to the config file

        :param path:
        :return:
        """
        Config.path = path

    @staticmethod
    def _retrieve_config_dict() -> dict:
        """
        Retrieves the settings dictionary

        :return: settings dictionary
        """
        with open(Config.path, "r") as f:
            for line in f.readlines():
                Config.settings.update({line.split(": ")[0]: line.split(": ")[1]})
        return Config.settings

    @staticmethod
    def get(path: str):
        """
        Retrieves the settings dictionary

        :param path: Path to the config file
        :return: settings dictionary
        """
        Config._set_path(path)
        settings = Config._retrieve_config_dict()
        return settings
