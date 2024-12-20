@echo off
rem activate venv
set cwd=%CD%
call env.bat
IF DEFINED VIRTUAL_ENV (goto end) ELSE (goto activate_venv)
:activate_venv
echo activate venv (Path %p_venv_default%)
cd %p_venv_default%
call activate.bat
cd %cwd%
:end
