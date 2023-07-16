@echo off
rem setlocal enabledelayedexpansion
rem this is to show case for interfacing to python programs vie single line printing 
rem allowing you to code more complex logic than in python

goto main

:set_envs
    echo Set Environment Variables 
    setlocal enabledelayedexpansion
    for %%f in (*.*) do (
        set /p value=<%%f
        set name=%%~nf
        echo Reading File [%%f] !value!
        set !name!=!value!
        rem call :set_env !name! !value!
    )    
    goto :processing

:main
@echo SET VARIABLES FROM BATCH
rem setting path of file as bat path
SET bat_path=%~dp0
SET bat_path=%bat_path:~0,-1%
rem setting the path of the python util file
SET util=python %bat_path%\lib_batch_helper\batch_util.py
rem setting the path where the variables are stored
SET config_path=%bat_path%\config
rem setting the path of the config file
SET config_txt=%bat_path%\config.txt
cd %bat_path%

@echo OPENING PATH [%util_path%] for batch_util.py
rem reading config.txt and transfer data as files in subfolder config
rem the file names correspomnd to environment variable names
@echo extracting variables from  [%config_txt%]
%util% --config %config_txt%
cd %config_path%
@echo ### Reading Files in Config Path [%config_path%]
goto :set_envs
:processing
@echo [%bat_path%]
rem cd %bat_path%
dir
rem check that data are set to environment 
rem if defined MY_VENV_DIR ( 
rem     @echo MY_VENV_DIR iS THERE %MY_VENV_DIR% 
rem ) else ( 
rem     @echo MY_VENV_DIR is not there 
rem )

rem display all my defined variablses 
rem set my_
rem %util% --env MY_VAR

