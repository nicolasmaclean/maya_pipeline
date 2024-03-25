#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Nick Maclean

:synopsis:
    System for running managed subprocesses.
"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Built-in
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
import os
import shutil
import subprocess

# 3rd Party
from PySide2.QtCore import QProcess

# External
from haymaker.enums import ResultType
from haymaker.log import log, Level
from haymaker.widgets import send_system_notification


#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#


def notify_system(process: 'ProcessResult'):
    """
    Sends a system notification though a tray icon.

    :param process: The result of a finished process.
    :type: ProcessResult
    """
    send_system_notification(
        title=f'{process.name}',
        message='Failure :(\nSee console for more info' if process.errors else 'Success!',
        icon=ResultType.FAILURE if process.errors else ResultType.SUCCESS
    )


#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#


@dataclass
class ProcessResult(object):
    """
    Data object for a finished subprocess.
    """
    name: str
    cmd: str
    args: [str]
    result: str
    errors: str


@dataclass
class Process(object):
    name: str
    exe: str
    args: [str]
    on_finish: Callable[[ProcessResult], None] = None

    stdout: int = subprocess.PIPE
    stderr: int = subprocess.PIPE

    is_finished: bool = field(default=False, init=False)
    results: (str, str) = field(default=None, init=False)
    _obj: QProcess = field(default=None, init=False)

    def run(self):
        """
        Creates the subprocess and starts it.

        :return: Successfully started
        :type: bool
        """
        self._obj = QProcess()
        self._obj.start(self.exe, self.args)
        self._obj.finished.connect(partial(self.finish, self._obj))
        started = self._obj.error() == QProcess.ProcessError.UnknownError

        # make sure the process is dead, if it failed to start
        if not started:
            self._obj.kill()

        return started

    def is_running(self) -> bool:
        return self._obj.state() == QProcess.Running

    def _get_result(self):
        result, errors = self._obj.readAllStandardOutput(), self._obj.readAllStandardError()
        self.results = result, (errors if errors else '')
        return self.results

    def finish(self, exit_code, exit_status):
        """
        Complete
        :return:
        """
        self.is_finished = True

        # log finish event
        result, errors = self._get_result()
        str_cmd = f'"{self.exe}" {" ".join(self.args)}'
        if errors:
            print(f'{self.name} subprocess failed: {str_cmd}')
            print(f'  {errors}')
        else:
            print(f'Finished "{self.name}" subprocess: {str_cmd}')

        # trigger finish callback
        if not self.on_finish:
            return
        result = ProcessResult(self.name, self.exe, self.args, result, errors)
        self.on_finish(result)


class AppExecuter(object):
    """
    Base system for running and managing subprocesses. Although this class can be
    used directly to run a subprocess, you probably want to derive from this and modify
    child.run()
    """
    NAME: str = 'Unnamed App Executer'
    NAME_EXE: str = None
    PROCESSES: [Process] = []

    def __init__(self, name=None, name_exe=None, path_exe=None):
        if name:
            self.NAME = name
        if name_exe:
            self.NAME_EXE = name_exe
        self.path_exe: str = path_exe

    @classmethod
    def _get_exe_path(cls, name_exe: str) -> str:
        """
        Gets the absolute path to the exe on path.

        :param name_exe: name of an exe (does not have to have the extension)
        :type: str

        :return: absolute path to .exe
        :type: str
        """
        return shutil.which(name_exe)

    def _create_process(self, args, on_finish) -> Process:
        process = Process(self.NAME, self.path_exe, args, on_finish)
        self.PROCESSES.append(process)
        return process

    def validate(self) -> bool:
        """
        Lazily collects and validates information necessary to run this executer.

        :return: True if self is valid
        :type: bool
        """
        # validate exe path
        if not self.path_exe:
            self.path_exe = self._get_exe_path(self.NAME_EXE)
            if not os.path.isfile(self.path_exe):
                return False

        return True

    def run(self, on_finish=None, *args, **kwargs):
        """
        Executes this task in a subprocess and send notification upon completion.

        :param on_finish: callback to perform upon execution completion
        :type: func(ProcessResult) -> None

        :param args: args passed to subprocess
        :param kwargs: kwargs passed to subprocess

        :return: the resulting subprocess
        :type: Popen
        """
        if not self.validate():
            return None

        # start subprocess
        args = list(args)
        for kwarg in kwargs:
            args.append(f'-{kwarg}')
            args.append(kwargs[kwarg])
        process = self._create_process(args, on_finish)
        started = process.run()

        # check the process was started successfully
        if not started:
            log(f'Failed to start process. Check {self.path_exe} exists.', Level.ERROR)

        return process, started
