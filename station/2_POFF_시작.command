#!/bin/zsh
# POFF · 영수증 스테이션 실행 (전시 중 이 창을 켜 두세요)
cd "$(dirname "$0")"
caffeinate -dimsu -w $$ &
/usr/bin/python3 server.py
