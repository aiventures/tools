@echo off
call env.bat
setlocal
set run_jar=java -jar %plantuml% -svg -stdrpt:1 -progress
rem if no file is given, transform all
if "%~1"=="" (set plantumlfile=*.plantuml) else (set plantumlfile=%1)
echo #### List of plantuml files
dir /b *.plantuml
echo GENERATE plantuml: %run_jar% %plantumlfile%
%run_jar% %plantumlfile%
echo _
endlocal

