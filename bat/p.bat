@echo off
rem p.bat setting a colored prompt with git branch and venv.

call colors.bat
set CURRENT_VENV=
set CURRENT_BRANCH=

python "C:\30_Entwicklung\WORK_JUPYTER\root\utils\src\util\utils.py"
if exist BRANCH.ENV ( goto set_current_branch ) else ( echo not a git directory )
:set_venv
if exist VENV.ENV ( goto set_current_venv ) else ( echo no VENV is set )

:check
if defined CURRENT_VENV (
  if defined CURRENT_BRANCH ( goto set_prompt_with_venv_with_branch  ) else ( goto set_prompt_with_venv_no_branch)
) else (
  if defined CURRENT_BRANCH ( set_prompt_no_venv_with_branch ) else ( goto set_prompt_no_venv_no_branch  )
)

:set_prompt_with_venv_with_branch
set PROMPT=%C_V%%CURRENT_VENV%%C_B%$s$c%CURRENT_BRANCH%$f$s%C_B%%C_P%$P%C_1%$G
goto end
:set_prompt_with_venv_no_branch
set PROMPT=%C_V%%CURRENT_VENV%%C_B%%C_B%%C_P%$P%C_1%$G

goto end
:set_prompt_no_venv_with_branch
set PROMPT=%C_B%$c%GIT_CURRENT_BRANCH%$f$s%C_B%%C_P%$P%C_0%$G  
goto end
:set_prompt_no_venv_no_branch
set PROMPT=%C_P%$P%C_0%$G
goto end

:set_current_branch
set /p CURRENT_BRANCH=< BRANCH.ENV
echo CURRENT_BRANCH %CURRENT_BRANCH%
goto set_venv
s
:set_current_venv
set /p CURRENT_VENV=< VENV.ENV
echo CURRENT_VENV %CURRENT_VENV%
goto check

:end
if exist BRANCH.ENV ( del BRANCH.ENV )
if exist VENV.ENV ( del VENV.ENV )
