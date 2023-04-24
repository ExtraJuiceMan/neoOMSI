import shlex


class OmsiQuestion:
    def __init__(
        self,
        question,
        number,
        filetype=".txt",
        flags="",
        compile_program="",
        compiler="",
        run_program="",
        run_cmd="",
    ):
        self.number = number
        self.filetype = filetype
        self.answer = "Write your answer here..."
        self.question = question
        self.flags = flags
        self.compile_program = compile_program
        self.run_program = run_program
        self.run_cmd = run_cmd
        self.compiler = compiler

    def get_question(self):
        return self.question

    def get_answer(self):
        return self.answer

    def get_filetype(self):
        return self.filetype

    def get_question_number(self):
        return self.number

    def set_answer(self, ans):
        self.answer = ans

    def get_flags(self):
        return self.flags.split(" ")

    def get_compile_program(self):
        return self.compile_program

    def get_compiler(self):
        return self.compiler

    def get_has_run(self):
        return self.run_program == "y"

    def get_run_cmd(self):
        return self.run_cmd.split(" ")


def parse_questions(filename):
    with open(filename, "r") as f:
        foundDescription = False
        firstQuestion = False

        question = ""
        questions = []
        line = f.readline()
        while line:
            if "DESCRIPTION" in line:
                foundDescription = True
                line = f.readline()
                while line and "DESCRIPTION" not in line and "QUESTION" not in line:
                    question += line
                    line = f.readline()
                q = OmsiQuestion(question, 0)
                questions.append(q)
                question = ""
            elif "QUESTION" in line:
                firstQuestion = True

                filetype = ".txt"
                flags = ""
                words = shlex.split(line)
                compileProgram = "n"
                compiler = ""
                runProgram = "n"
                runCmd = ""

                for i in range(len(words)):
                    if words[i] == "-ext":
                        if i + 1 >= len(words):
                            print("Error! Unexpected end of arguments...")
                        else:
                            print(("Setting type to {0}".format(words[i + 1])))
                            filetype = words[i + 1]
                        i += 1
                    if words[i] == "-flags":
                        if i + 1 >= len(words):
                            print("Error! Unexpected end of arguments...")
                        else:
                            fl = words[i + 1]
                            print(("Setting flags to {0}".format(fl)))
                            flags = fl
                    if words[i] == "-com":  # check if question can be compiled
                        if i + 1 >= len(words):
                            print("Error! Unexpected end of arguments...")
                        else:
                            com = words[i + 1]
                            print(("Setting compiler option to {0}".format(com)))
                            compileProgram = "y"
                            compiler = com
                    if words[i] == "-run":  # check if question can be run
                        if i + 1 >= len(words):
                            print("Error! Unexpected end of arguments...")
                        else:
                            runCmd = words[i + 1]
                            runProgram = "y"
                            print(("Setting run-command option to {0}".format(runCmd)))
                            runCmd = runCmd

                line = f.readline()
                while line and "DESCRIPTION" not in line and "QUESTION" not in line:
                    question += line
                    line = f.readline()
                q = OmsiQuestion(
                    question,
                    len(questions),
                    filetype,
                    flags,
                    compileProgram,
                    compiler,
                    runProgram,
                    runCmd,
                )
                questions.append(q)
                question = ""
            else:
                line = f.readline()
        return questions
