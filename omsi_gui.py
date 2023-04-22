import PySimpleGUI as sg
import base64
import argparse

from omsi_client import OmsiSocketClient, OmsiDataManager
from omsi_utility import parse_questions

WINDOW_ICON = base64.b64encode(open(r"matloff.png", "rb").read())


class Omsi:
    def __init__(self, hostname=None, port=None, email=None, id=None):
        self.questions = []
        self.combo_options = []
        self.omsi_client = None
        self.data = None
        self.selected_question = 0

        self.question_box = sg.Multiline(
            expand_y=True,
            expand_x=True,
            disabled=True,
            background_color="pale turquoise",
            font=("Courier New", 14),
        )

        self.answer_box = sg.Multiline(
            expand_y=True,
            expand_x=True,
            background_color="khaki",
            font=("Courier New", 14),
        )

        self.input_hostname = sg.Input(hostname, expand_x=True)
        self.input_port = sg.Input(port, expand_x=True)
        self.input_email = sg.Input(email, expand_x=True)
        self.input_id = sg.Input(id, expand_x=True)

        self.button_start = sg.Button("Start")
        self.button_pdf = sg.Button("Open PDF")
        self.button_graph = sg.Button("Open R Graph")
        self.button_help = sg.Button("About / Help")
        self.button_settings = sg.Button("Settings")
        self.button_exit = sg.Button("Exit")
        self.button_compile = sg.Button("Compile")
        self.button_run = sg.Button("Run")
        self.button_save = sg.Button("Save")
        self.button_submit = sg.Button("Submit", button_color="green")

        self.text_saved = sg.Text("Saved")
        self.text_connected = sg.Text(
            "Connected", visible=False, expand_x=True, expand_y=True
        )

        self.combo_question = sg.Combo(
            values=["No Session"],
            default_value="No Session",
            size=(35, 30),
            key="question_select",
            readonly=True,
            enable_events=True,
        )

        gui_left_column = [
            [sg.Image(source=WINDOW_ICON)],
            [
                sg.Text(
                    "Remember, I am\nalways watching.",
                    text_color="red",
                    auto_size_text=True,
                )
            ],
            [
                sg.Frame(
                    "Session",
                    [
                        [sg.Text("Hostname")],
                        [self.input_hostname],
                        [sg.Text("Port")],
                        [self.input_port],
                        [sg.Text("Email")],
                        [self.input_email],
                        [sg.Text("Exam ID")],
                        [self.input_id],
                        [self.button_start, self.text_connected],
                    ],
                )
            ],
            [sg.VPush()],
            [sg.HSeparator()],
            [self.button_pdf],
            [self.button_graph],
            [sg.HSeparator()],
            [self.button_help],
            [self.button_settings],
            [self.button_exit],
        ]

        gui_right_column = [
            [
                sg.Frame(
                    "Question",
                    [
                        [self.combo_question],
                        [self.question_box],
                    ],
                    expand_y=True,
                    expand_x=True,
                )
            ],
            [
                sg.Frame(
                    "Answer",
                    [
                        [
                            self.button_compile,
                            self.button_run,
                            self.button_save,
                            self.button_submit,
                            self.text_saved,
                        ],
                        [self.answer_box],
                    ],
                    expand_y=True,
                    expand_x=True,
                )
            ],
        ]

        gui_layout = [
            [
                sg.Column(
                    gui_left_column,
                    vertical_alignment="top",
                    element_justification="center",
                ),
                sg.Column(
                    gui_right_column,
                    expand_y=True,
                    expand_x=True,
                    vertical_alignment="top",
                ),
            ],
        ]

        self.window = sg.Window(
            "neoOMSI",
            gui_layout,
            default_element_size=(12, 1),
            auto_size_text=False,
            auto_size_buttons=False,
            default_button_element_size=(12, 1),
            resizable=True,
            element_justification="left",
            icon=WINDOW_ICON,
        )

    def show_error(self, message):
        sg.popup_ok(
            "Error\n" + message,
            title="Error",
            icon=WINDOW_ICON,
            no_titlebar=True,
            background_color="gray",
        )

    def start_session(self):
        hostname = self.input_hostname.get()
        port = self.input_port.get()
        email = self.input_email.get()
        id = self.input_id.get()

        if not port.isdigit():
            self.show_error("Port is not valid")
            return

        try:
            self.omsi_client = OmsiSocketClient(hostname, port, email, id)
            self.omsi_client.open()
        except Exception as e:
            self.show_error(f"Failed to open connection to server\n\n{e}")
            self.omsi_client.close()
            self.omsi_client = None
            return

        self.input_hostname.update(disabled=True, background_color="grey")
        self.input_port.update(disabled=True, background_color="grey")
        self.input_email.update(disabled=True, background_color="grey")
        self.input_id.update(disabled=True, background_color="grey")
        self.button_start.update(visible=False)
        self.text_connected.update(visible=True)

        self.data = OmsiDataManager(id)
        self.data.create_exam_dir()
        self.data.write_questions(self.omsi_client.get_exam_questions())
        # self.data.write_supp(self.omsi_client.get_supp_file())
        self.questions = parse_questions(self.data.questions_path())

        self.combo_options = [
            "Exam Information",
            *[f"Question {x}" for x in range(1, len(self.questions))],
        ]

        self.combo_question.update(values=self.combo_options)

        self.select_question(0)

    def select_question(self, index):
        if index == 0:
            self

        self.questions[self.selected_question].set_answer(self.answer_box.get())
        q = self.questions[index]
        self.question_box.update(value=q.get_question())
        self.answer_box.update(value=q.get_answer())
        self.combo_question.update(value=self.combo_options[index])
        self.selected_question = index

    def submit_answer(self, index):
        pass

    def save_answer(self, index):
        self.data.save_answer(self.questions[index])

    def is_in_exam(self):
        return self.omsi_client is not None

    def run(self):
        self.window.read(timeout=0)

        self.window.maximize()

        while True:
            event, values = self.window.read(timeout=10)

            if (
                event == sg.WIN_CLOSED
                or event == self.button_exit.key
                and sg.popup_ok_cancel(
                    "Are you sure you want to exit?",
                    title="Exit",
                    icon=WINDOW_ICON,
                    image=WINDOW_ICON,
                )
                == "OK"
            ):
                break

            if event == self.button_help.key:
                sg.popup_ok(
                    "neoOMSI\nUnofficial Just-For-Fun OMSI Client\n\nAuthor: ExtraConcentratedJuice",
                    title="About",
                )

            if event == self.button_start.key:
                self.start_session()

            if not self.is_in_exam():
                continue

            if event == self.combo_question.key:
                self.select_question(
                    self.combo_options.index(self.combo_question.get())
                )

            if event == self.button_save.key:
                self.save_answer(self.selected_question)

            if event == self.button_submit.key:
                self.submit_answer(self.selected_question)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="neoOMSI",
        description="Fun and better OMSI client that you probably shouldn't use",
    )

    parser.add_argument("hostname", nargs="?")
    parser.add_argument("port", nargs="?")
    parser.add_argument("email", nargs="?")
    parser.add_argument("id", nargs="?")

    args = parser.parse_args()

    Omsi(args.hostname, args.port, args.email, args.id).run()
