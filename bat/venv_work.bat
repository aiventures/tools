@echo off
rem activate venv
set cwd=%CD%
call env.bat
echo activate venv (Path %p_venv_default%)
cd %venv_work%
call activate.bat
cd %cwd%
