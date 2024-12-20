@echo off
rem open total commander at current location
call env.bat
set cwd=%cd%
set umo=%p_umo%
if "%~1"=="" (set rightdir=%umo%) else (set rightdir=%1)
echo OPEN TOTAL COMMANDER (%tc%) at "%cwd%"
rem https://stackoverflow.com/questions/5909012/windows-batch-script-launch-program-and-exit-console
start "" %tc% /O 1 /L="%cwd%" /R="%rightdir%"




