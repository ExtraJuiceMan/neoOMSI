import PySimpleGUI as sg
import base64
import argparse
import io
import subprocess
import time
import os
import random

from omsi_client import OmsiSocketClient, OmsiDataManager, VERSION
from omsi_settings import OmsiSettings
from omsi_utility import parse_questions

WINDOW_ICON = base64.b64encode(open(r"omsi.png", "rb").read())
SMALL_WINDOW_ICON = base64.b64encode(open(r"omsi_small.png", "rb").read())
MATLOFF = base64.b64encode(open(r"matloff.png", "rb").read())

CONNECT_END_KEY = "connect_end"
SUBMIT_END_KEY = "submit_end"

CONFIG_FILE = "omsi_settings.ini"

ABOUT = """
                          ___    __  __   ____    ___ 
  _ __     ___    ___    / _ \  |  \/  | / ___|  |_ _|
 | '_ \   / _ \  / _ \  | | | | | |\/| | \___ \   | | 
 | | | | |  __/ | (_) | | |_| | | |  | |  ___) |  | | 
 |_| |_|  \___|  \___/   \___/  |_|  |_| |____/  |___|


AUTHOR
ExtraConcentratedJuice

RESPOSITORY
https://github.com/ExtraConcentratedJuice/neoOMSI

ABOUT
A just-for-fun unoffical OMSI client implementation.
You probably shouln't use this on an actual exam.

HOTKEYS
OPEN PDF  CTRL + D
COMPILE   CTRL + C
RUN       CTRL + R
SAVE      CTRL + S
"""


class Omsi:
    def __init__(self, hostname=None, port=None, email=None, id=None, settings=None):
        self.questions = []
        self.combo_options = []
        self.omsi_client = None
        self.data = None
        self.connect_time = None
        self.selected_question = 0
        self.request_in_progress = False

        if settings is None:
            self.settings = OmsiSettings()
            self.settings.save(CONFIG_FILE)
        else:
            self.settings = settings

        self.question_box = sg.Multiline(
            expand_y=True,
            expand_x=True,
            disabled=True,
            background_color="pale turquoise",
            text_color="black",
            font=("Courier New", self.settings.font_size),
        )

        self.answer_box = sg.Multiline(
            key="answer_box",
            expand_y=True,
            expand_x=True,
            disabled=True,
            background_color="khaki",
            text_color="black",
            font=("Courier New", self.settings.font_size),
            enable_events=True,
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
        self.button_compile = sg.Button("Compile", disabled=True)
        self.button_run = sg.Button("Run", disabled=True)
        self.button_save = sg.Button("Save", disabled=True)
        self.button_submit = sg.Button("Submit", button_color="green", disabled=True)

        self.text_saved = sg.Text("Unsaved")
        self.text_connected = sg.Text(
            "Connected", visible=False, expand_x=True, expand_y=True, pad=(4, 4)
        )

        self.combo_question = sg.Combo(
            values=["No Session"],
            default_value="No Session",
            key="question_select",
            readonly=True,
            enable_events=True,
            auto_size_text=True,
        )

        gui_left_column = [
            [sg.Image(source="omsi.png")],
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

        self.event_dispatch_table = {
            self.button_help.key: self.show_about,
            self.button_start.key: self.start_session,
            self.button_settings.key: self.show_settings,
            **dict.fromkeys(
                [
                    sg.WINDOW_CLOSED,
                    sg.WINDOW_CLOSE_ATTEMPTED_EVENT,
                    self.button_exit.key,
                ],
                self.show_exit,
            ),
            self.button_pdf.key: self.open_pdf,
            self.button_graph.key: self.open_graph,
        }

        self.in_exam_dispatch_table = {
            self.combo_question.key: lambda: self.select_question(
                self.combo_options.index(self.combo_question.get())
            ),
            self.button_run.key: lambda: self.run_answer(self.selected_question),
            self.button_save.key: lambda: self.save_answer(self.selected_question),
            self.button_submit.key: lambda: self.submit_answer(self.selected_question),
            self.answer_box.key: lambda: self.update_save_status(False),
        }

        self.window = sg.Window(
            "neoOMSI",
            gui_layout,
            default_element_size=(14, 1),
            auto_size_text=False,
            auto_size_buttons=False,
            default_button_element_size=(14, 1),
            resizable=True,
            element_justification="left",
            icon=SMALL_WINDOW_ICON,
            disable_close=True,
        )

    def is_answers_disabled(self):
        return not self.is_in_exam() or self.selected_question == 0

    def is_in_exam(self):
        return self.omsi_client is not None

    def update_save_status(self, save=None):
        if len(self.questions) != 0:
            if save is None:
                save = self.questions[self.selected_question].get_was_saved()
            else:
                self.questions[self.selected_question].set_saved(save)

        self.text_saved.update(
            value="Saved" if save else "Unsaved",
            visible=self.selected_question != 0 and self.is_in_exam(),
        )

    def connect_start(self, hostname, port, email, id):
        if self.request_in_progress:
            return

        self.request_in_progress = True

        self.button_start.update("Connecting...", disabled=True)
        self.input_hostname.update(disabled=True)
        self.input_port.update(disabled=True)
        self.input_email.update(disabled=True)
        self.input_id.update(disabled=True)

        def connect():
            try:
                omsi_client = OmsiSocketClient(hostname, port, email, id)
                omsi_client.open()
                return omsi_client
            except Exception as e:
                omsi_client.close()
                return e

        self.window.perform_long_operation(connect, CONNECT_END_KEY)

    def connect_end(self, res):
        self.request_in_progress = False
        self.button_start.update("Start", disabled=False)

        if isinstance(res, Exception):
            self.input_hostname.update(disabled=False)
            self.input_port.update(disabled=False)
            self.input_email.update(disabled=False)
            self.input_id.update(disabled=False)
            self.show_error(f"Failed to open connection to server:\n{res}")
            return

        self.connect_time = time.time()
        self.omsi_client = res

        self.button_start.update(visible=False)
        self.text_connected.update(visible=True)

        self.data = OmsiDataManager(self.omsi_client.exam_id)
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

    def show_about(self):
        about_layout = [
            [
                sg.Text(
                    ABOUT + "\n\nVersion " + VERSION,
                    font=("Courier New", 14),
                    justification="center",
                )
            ],
            [
                sg.Image(MATLOFF),
                sg.Text(
                    "I am always watching...",
                    text_color="red",
                    font=("Courier New", 18),
                ),
            ]
            if self.is_in_exam()
            else [],
            [sg.Button("Close", bind_return_key=True)],
        ]

        about_window = sg.Window(
            "About", about_layout, icon=SMALL_WINDOW_ICON, finalize=True, modal=True
        )

        about_window.force_focus()

        return about_window.read(close=True)

    def show_error(self, message):
        error_layout = [
            [sg.VPush()],
            [sg.Image("error.png"), sg.Text(message.ljust(32))],
            [sg.VPush()],
            [sg.Button("OK", bind_return_key=True)],
        ]

        error_window = sg.Window(
            "Error", error_layout, icon=SMALL_WINDOW_ICON, finalize=True, modal=True
        )

        error_window.force_focus()

        return error_window.read(close=True)

    def show_settings(self):
        rpath_input = sg.Input(self.settings.r_path)
        pdf_reader_input = sg.Input(self.settings.pdf_reader_path)
        pdf_input = sg.Input(self.settings.pdf_path)
        font_size_input = sg.Spin(
            [x for x in range(4, 32)],
            self.settings.font_size,
        )

        layout = [
            [
                sg.Frame(
                    "Program/File Paths",
                    layout=[
                        [
                            sg.Text(
                                """If left empty, Rscript will be run using the 'Rscript' command and R needs to be on the PATH.
If left empty, PDFs will be opened with the 'open' command.
This will open the PDF using the default PDF viewer on your system."""
                            )
                        ],
                        [
                            sg.Text("Rscript Command/Path"),
                            sg.Push(),
                            rpath_input,
                            sg.FileBrowse(file_types=[["Executable", ".exe"]]),
                        ],
                        [
                            sg.Text("PDF Reader Command/Path"),
                            sg.Push(),
                            pdf_reader_input,
                            sg.FileBrowse(file_types=[["Executable", ".exe"]]),
                        ],
                        [
                            sg.Text("Reference PDF Path"),
                            sg.Push(),
                            pdf_input,
                            sg.FileBrowse(file_types=[["PDF", ".pdf"]]),
                        ],
                    ],
                    element_justification="left",
                )
            ],
            [
                sg.Frame(
                    "Preferences",
                    [
                        [
                            sg.Text("Editor Font Size"),
                            font_size_input,
                        ]
                    ],
                )
            ],
            [sg.Save(), sg.Cancel()],
        ]

        settings_window = sg.Window(
            "Settings", layout, modal=True, finalize=True, icon=SMALL_WINDOW_ICON
        )

        settings_window.force_focus()

        event, values = settings_window.read(close=True)

        if event == "Save":
            self.settings.r_path = rpath_input.get().strip()
            self.settings.pdf_reader_path = pdf_reader_input.get().strip()
            self.settings.pdf_path = pdf_input.get().strip()
            self.settings.font_size = font_size_input.get()

            self.answer_box.update(font=("Courier New", self.settings.font_size))
            self.question_box.update(font=("Courier New", self.settings.font_size))

            self.settings.save(CONFIG_FILE)

    def open_pdf(self):
        if not self.settings.pdf_path:
            self.show_error("No PDF reference file set in settings.")
            return

        if not os.path.exists(self.settings.pdf_path):
            self.show_error(
                f"The configured PDF path does not exist!\n{self.settings.pdf_path}"
            )
            return

        subprocess.Popen(
            [
                self.settings.pdf_reader_path or "open",
                self.settings.pdf_path,
            ]
        )

    def open_graph(self):
        if not os.path.exists("Rplots.pdf"):
            self.show_error("No graph to open.")
            return

        subprocess.Popen([self.settings.pdf_reader_path or "open", "Rplots.pdf"])

    def show_exit(self):
        exit_confirm = sg.Window(
            "Exit",
            [
                [sg.Image(WINDOW_ICON), sg.Text("Are you sure you want to exit?")],
                [sg.Button("Exit", button_color="red"), sg.Cancel()],
            ],
            icon=SMALL_WINDOW_ICON,
        )

        event, value = exit_confirm.read(close=True)

        if event == "Exit":
            exit()

    def start_session(self):
        hostname = self.input_hostname.get()
        port = self.input_port.get()
        email = self.input_email.get()
        id = self.input_id.get()

        if not hostname or not port or not email or not id:
            self.show_error("All fields must be filled.")
            return

        if not port.isdigit() or int(port) < 0 or int(port) >= 65535:
            self.show_error("Port is not valid.")
            return

        self.connect_start(hostname, port, email, id)

    def select_question(self, index):
        self.questions[self.selected_question].set_answer(self.answer_box.get())
        self.selected_question = index

        self.answer_box.update(
            value=self.questions[index], disabled=self.is_answers_disabled()
        )
        self.button_compile.update(
            disabled=self.is_answers_disabled()
            or not self.questions[index].get_compiler()
        )
        self.button_run.update(
            disabled=self.is_answers_disabled()
            or not self.questions[index].get_has_run()
        )
        self.button_save.update(disabled=self.is_answers_disabled())
        self.button_submit.update(disabled=self.is_answers_disabled())

        self.question_box.update(value=self.questions[index].get_question())
        self.answer_box.update(value=self.questions[index].get_answer())
        self.combo_question.update(value=self.combo_options[index])
        self.update_save_status()

    def submit_answer_start(self, index):
        if self.request_in_progress:
            return
        self.request_in_progress = True

        self.button_submit.update("Submitting...", disabled=True)
        self.combo_question.update(disabled=True)

        def submit():
            return self.omsi_client.send_file_with_retry(
                f"omsi_answer{self.questions[index].get_question_number()}{self.questions[index].get_filetype()}",
                io.BytesIO(self.questions[index].get_answer().encode("utf-8")),
            )

        self.window.perform_long_operation(submit, SUBMIT_END_KEY)

    def submit_answer_end(self, res):
        self.request_in_progress = False

        self.button_submit.update("Submit", disabled=False)
        self.combo_question.update(disabled=False)

        if isinstance(res, Exception):
            self.show_error(f"Failed to submit answer to server:\n{res}")
            return

        sg.popup_ok(
            "Server Response:\n" + res,
            title="Submission Result",
            icon=SMALL_WINDOW_ICON,
        )

    def submit_answer(self, index):
        if len(self.questions[index].get_answer()) == 0:
            self.show_error("No answer written.")
            return

        self.run_answer(index)
        self.submit_answer_start(index)

    def save_answer(self, index):
        self.questions[index].set_answer(self.answer_box.get())
        self.data.save_answer(self.questions[index])
        self.update_save_status(True)

    def run_answer(self, index):
        self.save_answer(index)

        if not self.questions[index].get_has_run():
            return

        run_cmd = self.questions[index].get_run_cmd()

        if run_cmd[0] == "Rscript" and self.settings.r_path:
            run_cmd[0] = self.settings.r_path

        try:
            proc = subprocess.Popen(
                run_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                self.show_error(
                    f"Could not run R interpreter: {' '.join(run_cmd)}.\nMake sure R is on the PATH or configure the executable's location in the settings.\n{e}"
                )
                return

            self.show_error(
                f"Failed to launch R interpreter: {' '.join(run_cmd)}\nError: {e}"
            )
            return

        out, _ = proc.communicate()

        sg.popup_scrolled(
            out.decode("utf-8"),
            title="Run - " + " ".join(run_cmd),
            non_blocking=True,
            icon=SMALL_WINDOW_ICON,
        )

    def event_loop(self, event, values):
        if event == CONNECT_END_KEY:
            self.connect_end(values[event])

        if event == SUBMIT_END_KEY:
            self.submit_answer_end(values[event])

        if event in self.event_dispatch_table:
            self.event_dispatch_table[event]()

        if self.is_in_exam():
            self.text_connected.update(
                value=time.strftime(
                    "Connected %H:%M:%S", time.gmtime(time.time() - self.connect_time)
                )
            )

            if event in self.in_exam_dispatch_table:
                self.in_exam_dispatch_table[event]()

    def run(self):
        self.window.read(timeout=0)

        self.window.bind("<Control-s>", self.button_save.key)
        self.window.bind("<Control-r>", self.button_run.key)
        self.window.bind("<Control-c>", self.button_compile.key)
        self.window.bind("<Control-d>", self.button_pdf.key)

        self.window.maximize()
        self.update_save_status()

        while True:
            self.event_loop(*self.window.read(timeout=5))


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

    Omsi(
        args.hostname, args.port, args.email, args.id, OmsiSettings.load(CONFIG_FILE)
    ).run()
