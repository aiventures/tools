@echo off
rem extract 1st argument from command line pass the rest
rem https://serverfault.com/questions/22443/do-windows-batch-files-have-a-construction
rem call env.bat
rem echo ### activate venv (Path %p_venv_default%)
rem call %p_venv_default%\activate.bat
rem echo ### RUN COMMAND [python %*]
rem python %*
set venv=%1
shift
set args=%1
:start
if [%1] == [] goto done
set args=%args% %1
shift
goto start
:done
echo VENV [%venv%] ARGS [%args%]