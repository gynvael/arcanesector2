@echo off
make -f Makefile.win32 -j 16
if not %errorlevel%  == 0 goto :eof

set ARCANE_PASSWD=WMgbi2F6RQzXOa09
set ARCANE_HOST=127.0.0.1:5001
echo type: r 2
gdb.exe client.exe

::start framedump.png


