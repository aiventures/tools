""" util to get input values from clipboard or input """
# simple input: either copies data from clipboard or from 
# input command and stores it in variable v
# this variable can be reused in other python utility programs 
# by using import 
# from simple_input import v
# to clean clipboard in windows: Use WIN+V

import win32clipboard
import win32ui

v = None

if v is None:
    # try to get path from clipboard
    win32clipboard.OpenClipboard()
    try:
        clipboard_data = win32clipboard.GetClipboardData()
    except TypeError:
        clipboard_data = None
    win32clipboard.CloseClipboard()

    if isinstance(clipboard_data,str):
        v = clipboard_data
    else:
        v = input("Enter value: ")

print(f"-- simple_input.py: Input Value set to <{v}> ---\n")