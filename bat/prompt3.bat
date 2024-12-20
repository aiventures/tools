@echo off
rem p: add colors and git branch and venv name to promp [GIT CURRENT BRANCH, VENV NAME]
rem prompt colors https://ss64.com/nt/syntax-ansi.html
rem get current branch from command
rem set GIT_CURRENT_BRANCH=
rem set cmd_git_branch=git branch --show-current
rem FOR /F "tokens=* USEBACKQ" %%F IN (`cmd_git_branch`) DO (SET GIT_CURRENT_BRANCH=%%F)
rem load color codes
rem echo "hugo"
rem echo %cmd_git_branch%
rem call colors.bat
rem echo hugo

rem set the new prompt _OLD_VIRTUAL_PATH is set by the activate script / when the VENV is activated so its an indicator of activated VENV
rem VENV_NAME needs to be set by the activation script could also be set by VIRTUAL_ENV_PROMPT
rem GIT_CURRENT_BRANCH is set 

rem if defined GIT_CURRENT_BRANCH 
echo hugo 
rem 
rem VENV is activated