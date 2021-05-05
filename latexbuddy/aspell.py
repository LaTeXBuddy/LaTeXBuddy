import shlex
import subprocess

from spellchecker import SpellChecker
from speller3x.checker import Checker


file_to_check = "/home/paul/Desktop/TestProject/main.tex"
language = "de"
language = shlex.quote(language)

# check which dictionaries are installed
t = subprocess.Popen(
    ["aspell dump dicts"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)

langs, errs = t.communicate()
langs = langs.decode("ISO8859-1")

print(langs)

# error if language dict not installed
if language not in langs:
    print(
        'Dict for language "'
        + language
        + '" not found - [Linux]Install via sudo apt install - check available dicts at https://ftp.gnu.org/gnu/aspell/dict/0index.html'
    )
    raise Exception("Spell check Failed")

# detex file and call aspell on detex output
error_list = subprocess.Popen(
    ["aspell -a" + " --lang=" + language + " < " + file_to_check],
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

# fetch aspell output
out, err_out = error_list.communicate()
out = out.decode("ISO8859-1")[70:]
out = out.split("\n")

for e in out:
    print(e)

# cleanup error list
cleaned_errors = []
for error in out:
    if error == "":
        error = "x"
    if error[0] == "&":
        cleaned_errors.append(error.replace("&", "").replace("\n", "").strip())
    if error[0] == "#":
        cleaned_errors.append(error.replace("#", "").replace("\n", "").strip())

print("---------------------------------------")
for e in cleaned_errors:
    print(e)
print("---------------------------------------")
print(cleaned_errors)

"""p = subprocess.Popen(["aspell -a" + " --lang=" + language + " < " + file_to_check], shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

#format aspell output
out, e = p.communicate()
out = out.decode("ISO8859-1")[70:].rstrip().replace("\n", "").split('&')

#print errors to console
for error in out:
    print(error.strip())"""
