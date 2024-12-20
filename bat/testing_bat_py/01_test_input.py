import os
_in = input("INPUT:")

with open('_testparam.bat', 'w') as file:
    file.write(f'SET TESTPARAM={_in}')
print("_test.bat saved")
