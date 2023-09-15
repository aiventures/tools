@echo off
rem define the file locations and rename the file to set_env_local.bat
rem code inspector python
set code_inspector=C:\<path to>\inspect_example.py
rem path to plantuml
set plantuml=java -jar C:\<path to>\plantuml.jar -DPLANTUML_LIMIT_SIZE=8192 -stdrpt:1 -progress
rem path to total commander
set tc=C:\<path to>\TOTALCMD64.EXE
rem path to your venv work 
set venv_work="C:\<path to>\<YOUR VENV>\Scripts\activate.bat"

