@echo off
rem activate local venv and start python program and pass all arguments 
call set_env_local.bat
echo activate venv (Path %venv_work%)
call %venv_work%
python %*