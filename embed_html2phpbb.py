""" utility to transform embed html code into phpbb code. You need to copy the embed code into 
    clipbboard, which is transformed into phpbb code and copyied back to clipboard
    (after an infobox is shown) , ready for paste ... 
    embed code can also be read from a file. Applicable for Windows OS.
"""

# %config IPCompleter.greedy=True # code completion, press tab after '.' / shift tab on command for docstring
# import required libs ...
import re
import sys
import requests
import urllib.parse
import locale
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import traceback
import win32clipboard
import win32ui

locale.setlocale(locale.LC_ALL, 'de_DE') # use German locale; name might vary with platform

# retrieve snippet from clipboard or from file
read_from_clipboard = True
# filename of code snippet 
snippet = r"C:\Users"
# Show detailed processing information
DEBUG = True

def phpbb_embed(tag,value,content):
    php_snippet = '['
    php_snippet += tag + '=' + value + ']' + content
    php_snippet += '[/' + tag + ']'        
    return php_snippet

def phpbb_wrap(tag,content):
    php_snippet = '[' + tag + ']' + content 
    php_snippet += '[/' + tag + ']'        
    return php_snippet

def get_soup_from_clipboard():
    # get clipboard data
    win32clipboard.OpenClipboard()
    clipboard_data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    soup = BeautifulSoup(clipboard_data, "html.parser")
    return soup

def get_soup_from_file(filename):
    try:
        with open(filename,'r',encoding='utf-8') as f:
            print("READ SNIPPET "+snippet)
            soup = BeautifulSoup(f,"html.parser")
        f.close()
        return soup   
    except:                
        print(traceback.format_exc())  

if read_from_clipboard is True:
    soup = get_soup_from_clipboard()
else:
    soup = get_soup_from_file(snippet)            

try:
    url_soup = soup.find("img")
    img_src = url_soup.attrs['src']
    title = url_soup.attrs['alt']
    url = soup.find("a").attrs['href']  
    inner = phpbb_wrap("img",img_src) + title + " (Klick macht gross)"
    print("PHPBB LINK")
    link = phpbb_embed("url",url,inner)
    tag = phpbb_embed("size","50","#foto_mw")
    link += tag    
except:          
    url_soup = None
    img_src = None
    title = None
    url = None   
    inner = None
    link = None
    tag = None
    # get clipboard data
    win32clipboard.OpenClipboard()
    clipboard_data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    link = str(BeautifulSoup(clipboard_data, "html.parser"))
    print(traceback.format_exc())  

if DEBUG is True:
    try:
        print("---------SNIPPET CONTENTS-----")
        print(soup)
        print("---------------------")
        print("IMG SRC:",img_src)
        print("TITLE:",title)
        print("URL:",url)
    except:
        print(traceback.format_exc())      

print(link)
# copy string to clipboard
df=pd.DataFrame([link])
df.to_clipboard(index=False,header=False)
print("Link copied to clipboard")
win32ui.MessageBox("Copied Clipboard Contents", "End Of Program")