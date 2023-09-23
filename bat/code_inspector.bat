@echo off
rem open plantuml with options
rem activate venv
call set_env_local.bat
call venv_work.bat
echo #### RUN Code Inspector (%code_inspector%)
setlocal
rem memorize current workdir 
set cwd=%CD%
rem get number of input params and process depending from it
set NUM_ARGS=0
for %%x in (%*) do Set /A NUM_ARGS+=1
echo NUMBER OF PARAMS %NUM_ARGS%
if %NUM_ARGS%==0 goto params0
if %NUM_ARGS%==1 goto params1

rem use 2 options, 1st param is option 2nd is path (may be enclosed in double quotes)
echo ### [2] PARAMS [path] ["option string"], use -h to display options
set options=%1
set options=%options:"=%
set params=%options% -p .
cd %2
echo changing to work directory %cd%

goto continue

rem no option used
:params0
echo ### [0] PARAMS - use default settings in current location
set params=
goto continue

rem one option used, use 
:params1
echo ### [1] PARAMS ["option string"] (%1)- use with options in current directory
set options=%1
if %options%==-h goto help
set options=%options:"=%
echo %options%
set params=%options% -p .
goto continue

:help
set params=-h

:continue
echo CALL CODE INSPECTOR
echo code_inspector %params% (Path %CD%)
python "%code_inspector%" %params%
echo switching back to path %cwd%, done 
cd %cwd%

endlocal

