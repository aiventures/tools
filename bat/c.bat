@echo off
rem activate local venv and start python command line client program and pass all arguments 
call env.bat
set cwd=%CD%
echo ### ACTIVATE DEFAULT ENV (Path %p_venv_default%)
cd %p_venv_default%
call activate.bat
cd %cwd%
python %py_cmd_client% %*
