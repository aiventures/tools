@echo off
rem open plantuml with options
rem parameters are simply passed

rem activate venv
call env.bat
echo ### activate venv (Path %p_venv_default%)
call %p_venv_default%\activate.bat

echo #### RUN Code Inspector (%py_code_inspector%)
setlocal
rem get number of input params and process depending from it
set NUM_ARGS=0
for %%x in (%*) do Set /A NUM_ARGS+=1
set params=%*
echo CALL CODE INSPECTOR with %NUM_ARGS% params [%params%]
python %py_code_inspector% %params%
endlocal

