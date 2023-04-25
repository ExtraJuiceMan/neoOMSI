import socket
import io
import os
import stat

from omsi_utility import OmsiQuestion

SOCKET_CHUNK_SIZE = 1024

COMMAND_GET_QUESTIONS = "ClientWantsQuestions"
COMMAND_GET_SUPP = "ClientWantsSuppFile"
RESPONSE_ACCEPT_READY = "ReadyToAcceptClientFile"

EXAM_QUESTIONS_FILE = "ExamQuestions.txt"
CODE_FILE = "code.R"
SUPP_FILE = "SuppFile"
VERSION = open("VERSION", "r").read()


class OmsiDataManager:
    def __init__(self, exam_id):
        self.exam_id = exam_id

    def create_exam_dir(self):
        if not os.path.exists("exams"):
            os.makedirs("exams")

        if not os.path.exists(self.get_exam_dir()):
            os.makedirs(self.get_exam_dir())

    def get_exam_dir(self):
        return os.path.join("exams", self.exam_id)

    def questions_path(self):
        return self.file_path(EXAM_QUESTIONS_FILE)

    def file_path(self, file):
        return os.path.join(self.get_exam_dir(), file)

    def write_buffer_to_file(self, path, buff: io.IOBase):
        with open(path, "wb") as f:
            f.write(buff.getbuffer())

    def write_questions(self, buff):
        self.write_buffer_to_file(self.file_path(EXAM_QUESTIONS_FILE), buff)

    def write_supp(self, buff):
        self.write_buffer_to_file(self.file_path(SUPP_FILE), buff)

    def write_code(self, buff):
        self.write_buffer_to_file(self.file_path(CODE_FILE), buff)

    def save_answer(self, question: OmsiQuestion):
        answer_file = f"omsi_answer{question.number}{question.get_filetype()}"

        with open(answer_file, "w") as f:
            os.chmod(
                answer_file,
                os.stat(answer_file).st_mode
                | stat.S_IXUSR
                | stat.S_IXGRP
                | stat.S_IXOTH,
            )
            f.write(question.get_answer())

        with open(self.file_path(answer_file), "w") as f:
            f.write(question.get_answer())


class OmsiSocketClient:
    def __init__(self, hostname, port, email, exam_id):
        self.hostname = hostname
        self.port = port
        self.email = email
        self.exam_id = exam_id
        self.socket = None

    def is_open(self):
        return self.socket is not None

    def open(self):
        if self.socket is not None:
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.hostname, int(self.port)))
        except:
            self.close()
            raise

    def close(self):
        if self.socket:
            self.socket.close()

        self.socket = None

    def receive_response(self):
        return self.socket.recv(SOCKET_CHUNK_SIZE).decode("utf-8")

    def receive_file(self):
        buffer = io.BytesIO()

        while True:
            chunk = self.socket.recv(SOCKET_CHUNK_SIZE)

            if chunk[-1] == 0:
                buffer.write(chunk[:-1])
                break

            buffer.write(chunk)

        return buffer

    def send_command(self, command):
        self.socket.send(command.encode())

    def get_exam_questions(self):
        self.open()
        self.send_command(COMMAND_GET_QUESTIONS)
        bytes = self.receive_file()
        self.close()
        return bytes

    def get_supp_file(self):
        self.open()
        self.send_command(COMMAND_GET_SUPP)
        bytes = self.receive_file()
        self.close()
        return bytes

    def send_file(self, file_name, file_bytes: io.IOBase = None):
        self.send_command(
            f"OMSI0001\0{file_name}\0{self.email}\0{VERSION}{self.exam_id}"
        )

        if self.receive_response() != RESPONSE_ACCEPT_READY:
            print("Server client desync")
            return

        while True:
            chunk = file_bytes.read(SOCKET_CHUNK_SIZE)

            if len(chunk) == 0:
                break

            self.socket.send(chunk)

        return self.receive_response()

    def send_file_with_retry(
        self, file_name, file_bytes: io.IOBase = None, max_tries=3
    ):
        attempts = 0
        err = None
        while attempts < max_tries:
            try:
                if not self.is_open():
                    self.open()

                return self.send_file(file_name, file_bytes)
            except socket.error as e:
                err = e
            finally:
                self.close()

            attempts += 1

        return err
