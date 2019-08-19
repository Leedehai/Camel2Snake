#!/usr/bin/env python

# This script changes variables names in C++ files from
# camelCase style to snake_case style
#
#
# Limitations caused by lack of syntax awareness:
#  a. it leaves variable initialized by ()-style (e.g. in constructor) untouched if the
#     variable does not end with an underscore, as it thinks the variable is a function:
#       what it does: variableName(initArgument) => variableName(init_argument)
#       it should do: variableName(initArgument) => variable_name(init_argument)
#  b. it replaces function name if it is used as a pointer, as it thinks the function
#     is a variable:
#       what it does: int (*funcPtr)(int, int) = &addInts; => int (*func_ptr)(int, int) = &add_ints;
#       it should do: int (*funcPtr)(int, int) = &addInts; => int (*func_ptr)(int, int) = &addInts;
#  c. it does not check name collision:
#       what it does: bool isGreek, bIsGreek; => bool is_greek, is_greek;
#       it should do: bool isGreek, bIsGreek; => bool is_greek, is_greek_2;

import os, sys
import re
import argparse

REGEX_PIECE_1 = r"(\A|(?<=\W))([a-jl-z]|[a-z]{2,})([A-Z][a-z]*|[0-9]+)+_?(?=[^\w\(]|$)"
REGEX_PIECE_2 = r"(\A|(?<=\W))([a-jl-z]|[a-z]{2,})([A-Z][a-z]*|[0-9]+)+_(?=\()"
DROMEDARY_CAMEL_CASE_VAR = re.compile(REGEX_PIECE_1 + "|" + REGEX_PIECE_2)

BOOLEAN_PREFIXES = [
    "is", "are", "was", "were",
    "has", "have", "had",
    "does", "do", "did", "done",
    "find", "found", "get", "got"
]
COMMON_ABBREVIATIONS = [ # NOTE no "num", "it", "src", "dest", "std", "ret"
    ("obj", "object"),  ("msg", "message"),  ("res", "result"), ("buf", "buffer"),
    ("vec", "vector"),  ("seq", "sequence"), ("cnt", "count"),  ("mem",  "memory"),
    ("ans", "answer"),  ("loc", "location"), ("elem", "element")
]

def compute_snake_case(camel_case, filepath="", testing=False):
    splitted_words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|[0-9]|_|$)|[0-9]+|\_", camel_case)
    if testing:
        print("'%s'\n\t=> %s" % (camel_case, splitted_words))
    if len(splitted_words) < 2:
        raise RuntimeError("len(splitted_words) < 2: '%s' => %s, in file %s" % (camel_case, splitted_words, filepath))
    if '_' in splitted_words[:-1]:
        raise RuntimeError("'_' inside '%s'[:-1], in file %s" % (camel_case, filepath))
    splitted_words = list(map(lambda w : w.lower(), splitted_words))
    # special rules in conversion
    ends_with_underscore = False
    if splitted_words[-1] == '_':
        splitted_words = splitted_words[:-1]
        ends_with_underscore = True
    if (splitted_words[0] == "p" or splitted_words[0] == "m"
        or splitted_words[0] == "n" or splitted_words[0] == "f"):
        splitted_words = splitted_words[1:]
    if splitted_words[0] == "b":
        if splitted_words[1] in BOOLEAN_PREFIXES:
            splitted_words = splitted_words[1:]
        else:
            splitted_words = [ "is" ] + splitted_words[1:]
    if splitted_words[0] == "it":
        splitted_words = [ "iter" ] + splitted_words[1:]
    if splitted_words[-1] == "num":
        splitted_words = splitted_words[:-1] + [ "number" ]
    for e in COMMON_ABBREVIATIONS:
        splitted_words = list(map(lambda w : e[1] if w == e[0] else w, splitted_words))
    # make snake_case
    snake_case = '_'.join(splitted_words) + ('_' if ends_with_underscore else '')
    return snake_case

MAX_LOOP_STEPS = 16 # unlikely to have more than this number of camelCase variables in one line
def process_one_line(old_line, filepath, testing=False):
    step_count, instance_count = 0, 0
    line = old_line
    while True:
        step_count += 1
        if step_count > MAX_LOOP_STEPS:
            raise RuntimeError("maximum loop steps (%d) exceeded, line: '%s'" % (
                MAX_LOOP_STEPS, old_line))
        matchObj = re.search(DROMEDARY_CAMEL_CASE_VAR, line)
        if not matchObj:
            return line, instance_count
        camel_case_var = matchObj.group(0)
        camel_case_var_start, camel_case_var_end = matchObj.start(), matchObj.end()
        instance_count += 1
        snake_case_var = compute_snake_case(camel_case_var, filepath, testing)
        line = line[:camel_case_var_start] + snake_case_var + line[camel_case_var_end:]

def process_one_file(filepath, echo, rewrite):
    with open(filepath, 'r') as f:
        raw_lines = f.readlines()
    instance_count, new_lines = 0, []
    for raw_line in raw_lines:
        old_line = raw_line.rstrip()
        if echo:
            print("\x1b[38;5;217m" + old_line + "\x1b[0m")
        new_line, instance_count_in_line = process_one_line(old_line, filepath)
        if echo:
            print("\x1b[32m" + new_line + "\x1b[0m")
        new_lines.append(new_line)
        instance_count += instance_count_in_line
    if rewrite:
        with open(filepath, 'r') as f:
            f.write('\n'.join(new_lines) + '\n')
    return instance_count

def is_c_cxx(filename):
    if (filename.endswith(".h") or filename.endswith(".cc")
        or filename.endswith(".cpp") or filename.endswith(".c")):
       return True
    return False

def work(args):
    if args.test != None:
        new_line, _ = process_one_line(args.test, filepath=None, testing=True)
        print("\x1b[32;m" + new_line + "\x1b[0m")
        return
    files_to_read = [] if os.path.isdir(args.path) else [ args.path ]
    if len(files_to_read) == 0:
        for (dirpath, dirnames, filenames) in os.walk(args.path, followlinks=True):
            for filename in filter(lambda f : is_c_cxx(f), filenames):
                if (((os.sep + "test-inputs") in dirpath)
                    or ((os.sep + "third-party") in dirpath)
                    or ((os.sep + "linters") in dirpath)):
                    continue
                files_to_read.append(os.path.join(dirpath, filename))
    for filepath in files_to_read:
        sys.stdout.write("%s .." % (filepath))
        sys.stdout.flush()
        processed_instances = process_one_file(filepath, echo=args.echo, rewrite=args.rewrite)
        sys.stdout.write("\r%s count: %d\n" % (filepath, processed_instances))
        sys.stdout.flush()
    return 0

def main():
    parser = argparse.ArgumentParser(description="C/C++ vairable name camelCase => snake_case")
    parser.add_argument("-p", "--path", type=str, default=None,
                        help="file or directory path")
    parser.add_argument("--rewrite", action="store_true",
                        help="rewrite visited files")
    parser.add_argument("-e", "--echo", action='store_true',
                        help="(dev) echo each line")
    parser.add_argument("-t", "--test", metavar="\"..\"", type=str, default=None,
                        help="(dev) test one line")
    args = parser.parse_args()
    has_error = False
    if args.test == None and args.path == None:
        has_error = True
        print("[Error] you need to use either '--path' or '--test'")
    if args.test != None and (args.path != None or args.rewrite or args.echo):
        has_error = True
        print("[Error] '--test' can only be used alone")
    if (args.rewrite or args.echo) and args.path == None:
        has_error = True
        print("[Error] specify path using '--path'")
    if args.path != None and not os.path.exists(args.path):
        has_error = True
        print("[Error] not found: %s" % args.path)
    return 1 if has_error else work(args)

if __name__ == "__main__":
    sys.exit(main())