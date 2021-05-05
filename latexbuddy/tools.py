import subprocess


# example usage in aspell.py
def execute(*cmd):
    command = ""
    for arg in cmd:
        command += arg + " "
    command.strip()

    error_list = subprocess.Popen(
        [command], shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    out, err_out = error_list.communicate()
    return out.decode("ISO8859-1")


def detex(file_to_detex):
    detexed_file = file_to_detex + ".detexed"
    execute("detex", file_to_detex, " > ", detexed_file)
    return detexed_file
