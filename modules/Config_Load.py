import configparser
import os


class C_Config():
    def __init__(self):
        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join(os.path.dirname(__file__), r"./config.ini"))

    def load(self, count):
        section = self.conf_parser.sections()[count]
        options = self.conf_parser.options(section)
        config = dict()
        for option in options:
            config[option] = self.conf_parser.get(section, option)
        return config
