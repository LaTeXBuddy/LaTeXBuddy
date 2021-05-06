import subprocess


# example usage in aspell.py
def execute(*cmd: str) -> str:
    command = get_command_string(cmd)

    error_list = subprocess.Popen(
        [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    out, err_out = error_list.communicate()
    return out.decode("ISO8859-1")


def execute_from_list(cmd: list[str]) -> str:
    return execute(*cmd)


def execute_background(*cmd: str) -> subprocess.Popen:
    command = get_command_string(cmd)

    process = subprocess.Popen(
        [command], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return process


def execute_background_from_list(cmd: list[str]) -> subprocess.Popen:
    return execute_background(*cmd)


def get_command_string(*cmd: str) -> str:
    command = ""
    for arg in cmd:
        command += arg + " "
    return command.strip()


def detex(file_to_detex):
    detexed_file = file_to_detex + ".detexed"
    execute("detex", file_to_detex, " > ", detexed_file)
    return detexed_file


if __name__ == "__main__":
    command_ = ["echo", "hi,", "what\\'s", "up?"]
    print(execute(*command_))
    # print(execute_from_list(command_))
