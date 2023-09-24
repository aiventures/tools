@echo off
rem open plantuml with options
rem parameters are simply passed
rem activate venv
call set_env_local.bat
call venv_work.bat
echo #### RUN Code Inspector (%code_inspector%)
setlocal
rem get number of input params and process depending from it
set NUM_ARGS=0
for %%x in (%*) do Set /A NUM_ARGS+=1
set params=%*
echo CALL CODE INSPECTOR with %NUM_ARGS% params [%params%]
python "%code_inspector%" %params%
endlocal

