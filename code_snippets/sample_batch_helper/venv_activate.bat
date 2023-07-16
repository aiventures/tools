@echo off
rem setlocal enabledelayedexpansion / do not use this 
rem sample to read environment vars from config subfolder 
rem usage use start venv_activate.bat envname to activate environemnt and 
rem start in work dir repo if it has the same name as the repo
goto :main

:set_env
rem sets environment variables from stored files
    set var=%~1
    set %var%=
    IF EXIST %config_path%\%var% (
        set /P %var%=<%config_path%\%var%
        @echo   * Set ENV %var%
    ) else (
      @echo FILE %var% not found in %config_path%
    )
exit /b

:venv_activate
    set MY_VENV_PATH=%MY_VENV_DIR%\%~1
    set MY_VENV=
    IF EXIST "%MY_VENV_PATH%" (
        @echo ### Environment %venv_path%
        if defined VIRTUAL_ENV (
          @echo     Deactivate VENV %VIRTUAL_ENV%                    
          deactivate
        )
        @echo     Activate %~1 [%MY_VENV_PATH%]
        %MY_VENV_PATH%\Scripts\activate.bat
    ) else (
      @echo ERROR %~1 is not a valid Environment
      set %MY_VENV_PATH%=
    )    
exit /b

:cd_workdir
    if defined MY_WORK_DIR (
      rem check if there is a workdir with the same name as the environment 
      cd %MY_WORK_DIR%
      if defined MY_VENV_DIR (
        if exist %MY_VENV_DIR%\%MY_VENV% (
          echo ### WORK DIR FOR ENV [%MY_VENV%] [%MY_VENV_DIR%\%MY_VENV%]
          cd %MY_VENV_DIR%\%MY_VENV%
        )
      )
    ) else (
      @echo VARIABLE MY_VENV_DIR is not defined can't navigate
    )
exit /b

:main
@@echo ### SET VARIABLES FROM FILE
rem setting path of file as bat path
SET bat_path=%~dp0
SET bat_path=%bat_path:~0,-1%
rem setting the path where the variables are stored
SET config_path=%bat_path%\config
set MY_VENV_DIR=
set MY_WORK_DIR=
rem batch is called using the venv name
set MY_VENV=%1
call :set_env MY_VENV_DIR
call :set_env MY_WORK_DIR
call :cd_workdir
rem ORDER is important call venv activate as last call then everything is working fine
call :venv_activate %1





