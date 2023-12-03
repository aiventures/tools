@echo off
rem read a file line by line
for /f "tokens=*" %%a in (list.txt) do (
  echo line=%%a
)

pause