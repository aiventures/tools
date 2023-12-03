@echo off
rem activate local venv and start python program and pass all arguments 
rem env.bat can be created using the command line client, see runner.py
call env.bat
echo ### activate venv (Path %p_venv_default%)
call %p_venv_default%\activate.bat
echo ### RUN COMMAND [python %*]
python %*