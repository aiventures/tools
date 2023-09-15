@echo off
rem open total commander at current location
call set_env_local.bat
setlocal
set cwd=%cd%
set umo=C:\05_TRANSIENT\Henrik\_UMO
if "%~1"=="" (set rightdir=%umo%) else (set rightdir=%1)
echo OPEN TOTAL COMMANDER (%tc%) at "%cwd%"
start %tc% /O /L="%cwd%" /R="%rightdir%"
endlocal

