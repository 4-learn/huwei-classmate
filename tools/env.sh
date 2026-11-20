# source 這支讓 headless chromium 找得到系統庫與中文字型
L=/home/dsh/workspace/.da-tools/libs
export LD_LIBRARY_PATH=$L/usr/lib/x86_64-linux-gnu:$L/lib/x86_64-linux-gnu
export FONTCONFIG_PATH=$L/etc/fonts
