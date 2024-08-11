""" Cnd Runner: Runs OS Commands locally """
import sys
import os
import subprocess
import shlex
import logging

logger = logging.getLogger(__name__)

class CmdRunner():
    """ Cnd Runner: Runs OS Commands locally """

    def __init__(self,cwd:str=None) -> None:
        """ constructor """
        self._output=None
        self._return_code=0
        if not cwd:
            cwd = os.getcwd()
        if not os.path.isdir(cwd):
            logger.error(f"{cwd} is not a path, check input")
        self._cwd = os.path.abspath(cwd)

    def run_cmd(self,os_cmd:str):
        """ runs command line command """        
        logger.info(f"RUN COMMAND [{os_cmd}]")
        if not os_cmd:
            logger.warning("No command submitted, return")
            return
        oscmd_shlex=shlex.split(os_cmd)
        # special case: output contains keywords (in this case its displaying a logfile)
        self._output=[]
        self._return_code=0
        try:
            # encoding for german umlauts
            with subprocess.Popen(oscmd_shlex, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    errors='ignore',universal_newlines=True,encoding="utf8",cwd=self._cwd) as popen:
                for line in popen.stdout:
                    self._output.append(line)
                    line=line.replace("\n","")
                    logger.info(line)

            # popen.stdout.close()
            if popen.stderr:
                logger.error(f"ERROR OCCURED: {popen.stderr}")

            self._return_code = popen.returncode
            if self._return_code:
                raise subprocess.CalledProcessError(self._return_code, os_cmd)
        except subprocess.CalledProcessError as e:
            self._return_code=1
            logger.error(f"EXCEPTION OCCURED {e}, command {os_cmd}")
        return self._return_code

    def get_output(self,as_string=True):
        """ Returns output from last command
        Args:
            as_string (bool, optional): if True, output string list will be concatenated. Defaults to True.
        Returns:
            string/list: single output strings as list or concatenated string
        """
        out=self._output
        if as_string and isinstance(out,list):
            out = "".join([l.strip() for l in out])
        return out

if __name__ == "__main__":
    loglevel = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s:[%(name)s.%(funcName)s(%(lineno)d)]: %(message)s',
                        level=loglevel, stream=sys.stdout, datefmt="%Y-%m-%d %H:%M:%S")
