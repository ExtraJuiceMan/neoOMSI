import configparser
import configparser


class OmsiSettings:
    def __init__(
        self,
        r_path="",
        pdf_reader_path="",
        pdf_path="",
        font_size=14,
    ):
        self.r_path = r_path
        self.pdf_reader_path = pdf_reader_path
        self.pdf_path = pdf_path
        self.font_size = font_size

    def save(self, filename):
        config = configparser.ConfigParser()
        config["Options"] = {
            "r_path": self.r_path,
            "pdf_reader_path": self.pdf_reader_path,
            "pdf_path": self.pdf_path,
            "font_size": self.font_size,
        }

        with open(filename, "w") as f:
            config.write(f)

    def load(filename):
        config = configparser.ConfigParser()

        if not config.read(filename):
            return None

        o = config["Options"]

        r_path = o["r_path"]
        pdf_reader_path = o["pdf_reader_Path"]
        pdf_path = o["pdf_path"]
        font_size = o["font_size"]

        return OmsiSettings(r_path, pdf_reader_path, pdf_path, font_size)
