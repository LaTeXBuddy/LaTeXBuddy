import shlex
import subprocess
import tools

file_to_check = "/home/paul/Desktop/TestProject/main.tex"
language = "de"
language = shlex.quote(language)

#check which dictionaries are installed
"""langs = subprocess.Popen(["aspell dump dicts"], shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)"""

langs = tools.execute("aspell", "dump dicts", False)

#error if language dict not installed
if language not in langs:
    print("Dict for language \"" + language + "\" not found - [Linux]Install via sudo apt install - check available dicts at https://ftp.gnu.org/gnu/aspell/dict/0index.html")
    raise Exception("Spell check Failed")

#detex file and call aspell on detex output
error_list = tools.execute("aspell -a --lang=" + language + " < " + file_to_check)

#fetch aspell output
out = error_list.communicate()
out = out.decode("ISO8859-1")[70:]
out = out.split("\n")

for e in out:
    print(e)

#cleanup error list
cleaned_errors = []
for error in out:
    if error == "":
        error = "x"
    if error[0] == '&':
        cleaned_errors.append(error.replace("&", "").replace("\n", "").strip())
    if error[0] == '#':
        cleaned_errors.append(error.replace("#", "").replace("\n", "").strip())
