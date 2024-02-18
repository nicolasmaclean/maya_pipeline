#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    Basic logger with minimal formatting.
"""
import json
import string
#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-In
from enum import Enum
import inspect
import os
import sys
from time import localtime, strftime

# Third Party
try:
    import maya.cmds as cmds
    MAYA = True
except ImportError:
    MAYA = False

# Internal
from haymaker.formula_manager import eval_formula

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------- ENUMS --#


class Level(Enum):
    TRACE = 'Trace'
    INFO = 'Info'
    WARN = 'Warning'
    ERROR = 'Error'


#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def log(message, level=Level.INFO, step_back=2, width=120):
    trace = _build_trace(step_back)

    _log_to_file(message, level, trace)
    _log_to_console(message, level, trace, width)


def submit_log():
    global _path_log
    if not _path_log:
        _start_log()

    log_name = os.path.join(os.getlogin(), os.path.basename(_path_log))
    path_report = eval_formula('f_log_report')
    os.makedirs(os.path.dirname(path_report), exist_ok=True)
    with open(path_report, 'a') as file:
        file.write(f'- [ ] {log_name}\n')


def _log_to_console(message, level, trace, width):
    time_str = strftime("%H:%M:%S", localtime())

    # noinspection PyTypeChecker
    s = f'{time_str}  [{level.value.upper()}]  '
    indent = ''.join([' ' for _ in s])
    lines = []

    # wrap lines to fit width
    for c in message:
        s += c
        if c == '\n' or len(s) >= width:
            lines.append(s)
            s = indent

    # send to console
    lines.append(s)
    print('\n'.join(lines))

    if level == Level.TRACE or level == Level.INFO:
        return

    # show stack trace, for warnings/errors
    for frame in trace:
        file = frame['file']
        line = frame['line']
        function = frame['function']
        context = frame['context']
        print(f'  File "{file}", line {line}, in {function}')
        if context:
            print(f'    {context.lstrip()}')


def _log_to_file(message, level, trace):
    # lazy-load log file
    global _file_log
    if not _file_log:
        _start_log()

    # format message
    data = {
        'date': strftime("%Y-%m-%d %H-%M-%S", localtime()),
        'level': level.value,
        'message': message,
        'trace': trace,
    }
    str_data = json.dumps(data) + '\n'

    # send to log
    _file_log.write(str_data)

    # save file immediately (because we leave it)
    _file_log.flush()
    os.fsync(_file_log.fileno())


def _build_trace(steps_back=2):
    stack = iter(inspect.stack())
    for i in range(steps_back):
        next(stack)

    trace = []
    for frame in stack:
        # if frame.function == '<module>':
        #     continue
        trace.append({
            'file': frame.filename,
            'line': frame.lineno,
            'function': frame.function,
            'context': frame.code_context[0][:-1] if frame.code_context else None,
        })

    return trace


_path_log = None
_file_log = None
def _start_log():
    # close the previous log
    # this shouldn't happen outside a developer context
    global _file_log
    global _path_log
    if _file_log:
        _file_log.close()

    # build log path
    user = os.getlogin().lower()
    time_str = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    log_name = f'{time_str}.log'
    _path_log = eval_formula('f_log', user=user, name=log_name)

    # create empty log file
    os.makedirs(os.path.dirname(_path_log), exist_ok=True)
    _file_log = open(_path_log, 'w')

    _show_startup_info()


def _show_startup_info():
    log(f'Starting log for {os.getlogin()}...')

    if MAYA:
        maya_version = cmds.about(version=True)
        maya_os = cmds.about(operatingSystem=True)
        log(f'Maya {maya_version}: {maya_os}')

    log(f'Python {sys.version}')


#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#

#----------------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------- MAIN --#


def main():
    log('hi')


if __name__ == '__main__':
    main()
