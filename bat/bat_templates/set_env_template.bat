@echo off
rem define the file locations and rename the file to set_env_local.bat
rem ensure that the files are accessible from the Path 
rem code inspector python
rem note use the cmd_client to create environment variables directly 
set code_inspector=C:\<path to>\inspect_example.py
rem path to plantuml
set plantuml=java -jar C:\<path to>\plantuml.jar -DPLANTUML_LIMIT_SIZE=8192 -stdrpt:1 -progress
rem path to total commander
set tc=C:\<path to>\TOTALCMD64.EXE
rem path to your venv work 
set venv_work="C:\<path to>\<YOUR VENV>\Scripts\activate.bat"

