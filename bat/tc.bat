@echo off
rem open total commander at current location
call env.bat
setlocal
set cwd=%cd%
set umo=%p_umo%
if "%~1"=="" (set rightdir=%umo%) else (set rightdir=%1)
echo OPEN TOTAL COMMANDER (%tc%) at "%cwd%"
%tc% /O 1 /L="%cwd%" /R="%rightdir%"
endlocal

