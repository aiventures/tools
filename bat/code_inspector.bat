@echo off
rem activate venv
call set_env_local.bat
call venv_work.bat
echo #### RUN Code Inspector (%code_inspector%)
setlocal
rem if no file is given, transform all
if "%~1"=="" (set workdir=%CD%) else (set workdir=%1)
echo %code_inspector% %workdir%
python %code_inspector% %workdir%
rem OPEN TOTAL COMMANDER
tc %workdir%
endlocal

