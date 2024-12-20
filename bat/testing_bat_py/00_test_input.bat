SET TESTPARAM=
python _test_input.py
call _testparam.bat
SET TEST
echo %TESTPARAM%
python _testenviron.py