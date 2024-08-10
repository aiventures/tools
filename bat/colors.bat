@echo off
rem colors.bat: Sets specific color codes as ENV C... (check using C_set C_), also see colors.py
ren https://en.wikipedia.org/wiki/ANSI_escape_code
rem https://ss64.com/nt/syntax-ansi.html
rem https://stackoverflow.com/questions/2048509/how-to-echo-with-different-colors-in-the-windows-command-line 
rem https://gist.github.com/mlocati/fdabcaeb8071d5c75a2d51712db24011#file-win10colors-cmd
rem define a newline variable (spaces need to be kept)
rem https://stackoverflow.com/questions/132799/how-can-i-echo-a-newline-in-a-batch-file

rem create an ESQ Sequence
for /F %%a in ('echo prompt $E ^ cmd") do set "ESC=%%a"
rem selected color palette (38 is foreground, 48 is background), use py_color_list.bat to display the pytho
set COL_GREEN_DARK=%ESC%[38;5;34m 
set COL_GREEN=%ESC%[38;5;40m
set COL_GREEN_LIGHT=%ESC%[38;5;46m
set COL_ORANGE_DARK=%ESC%[38;5;202m
set COL_ORANGE=%ESC%[38;5;208m
set COL_ORANGE_LIGHT=%ESC%[38;5;214m
set COL_YELLOW=%ESC%[38;5;220m
set COL_YELLOW_LIGHT=%ESC%[38;5;226m
set COL PINK_DARK=%ESC%[38;5;200m
set COL_PINK=%ESC%[38;5;206m
set COL_PINK_LIGHT=%ESC%[38;5;212m
set COL_BLUE_DARK=%ESC%[38;5;33m
set COL_BLUE=%ESC%[38;5;39m
set COL_BLUE_LIGHT=%ESC%[38;5;45m
set COL_BLUE_SKY=%ESC%[38;5;75m
set COL_PURPLE=%ESC%[38;5;99m
set COL_PURPLE_LIGHT=%ESC%[38;5;105m
set COL_GREY_DARK=%ESC%[38:5:242m
set COL_GREY=%ESC%[38;5;246m
set COL_GREY_LIGHT=%ESC%[38;5;249m
set COL_WHITE=%ESC% [38;5;255m
set COL_BLACK=%ESC% [38;5;232m
rem bright colors are 90-97 / std colors are 30-37
set C_0=%ESC%[0m
set C_GRY=%ESC%[90m
set C_RED=%ESC%[91m
set C_GRN=%ESC%[92m
set C_YLL=%ESC%[93m
set C_BLU=%ESC%[94m
set C_MAG=%ESC%[95m
set C_CYN=%ESC%[96m
set C_WHT=%ESC%[97m
rem specific colors for branch path venv
rem prompt branch color
set C_B=%COL_GREEN_DARK%
rem prompt path color
set C_P=%COL_ORANGE%
rem prompt venv color
set C_V=%COL_BLUE_SKY%
rem different text colors when activated
set C_0=%C_0%
set C_1=%C_WHT%
rem set colors for certain echos
rem title
set C_T=%COL_GREEN%
rem search keys
set C_S=%COL_ORANGE%
rem file keys
set C_F=%COL_BLUE_SKY%
rem python output
set C_PY=%C_GRN%
rem question / prompt
set C_Q=%C_MAG%
