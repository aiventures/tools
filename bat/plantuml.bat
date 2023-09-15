@echo off
call set_env_local.bat
setlocal
rem if no file is given, transform all
if "%~1"=="" (set plantumlfile=*.plantuml) else (set plantumlfile=%1)
echo #### List of plantuml files
dir /b *.plantuml
echo GENERATE plantuml: %plantuml% %plantumlfile%
%plantuml% %plantumlfile%
endlocal

