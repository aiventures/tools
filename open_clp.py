"""Open application/file/folder from string stored in clipboard"""
import webbrowser
import win32ui
import os
from pathlib import Path, PureWindowsPath
from tools.simple_input import v
p = v
showinfo = True
# remove apostrophes and carriage return
p = p.replace('"','')
p = p.replace('\r\n','')
if showinfo:
    print(f"input: {p}")

if (p[:4] == "http"):
    webbrowser.open(p)
else:
    try:
        os.startfile(p)
    except Exception as e:
        s = f"Input Error\n"+str(e)
        win32ui.MessageBox(s, "End Of Program")

