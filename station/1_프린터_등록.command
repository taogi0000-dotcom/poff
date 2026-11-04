#!/bin/zsh
# POFF · 영수증 프린터를 맥에 한 번만 등록하는 스크립트
cd "$(dirname "$0")"
echo ""
echo "  POFF · 영수증 프린터 등록"
echo "  프린터를 USB로 맥북에 연결하고 전원을 켠 상태여야 해요."
echo "  (맥 로그인 비밀번호를 물어보면 입력해 주세요. 입력해도 화면엔 안 보여요.)"
echo ""
URIS=("${(@f)$(sudo lpinfo -v 2>/dev/null | awk '$1=="direct" && $2 ~ /^usb:/ {print $2}')}")
URIS=(${URIS:#})
if [ ${#URIS[@]} -eq 0 ]; then
  echo "  ✗ USB 프린터를 찾지 못했어요. 케이블 · 전원 · 젠더를 확인하고 다시 실행해 주세요."
  read -k1 "?  아무 키나 누르면 닫혀요"; exit 1
fi
echo "  찾은 USB 프린터:"
i=1; for u in $URIS; do echo "   $i) $u"; i=$((i+1)); done
if [ ${#URIS[@]} -eq 1 ]; then n=1; else read "n?  사용할 번호를 입력하세요: "; fi
URI=${URIS[$n]}
PPD=$(find /System/Library/Frameworks/ApplicationServices.framework -name Generic.ppd 2>/dev/null | head -1)
sudo lpadmin -x POFF_RECEIPT 2>/dev/null
if [ -n "$PPD" ]; then
  sudo lpadmin -p POFF_RECEIPT -E -v "$URI" -P "$PPD" -o printer-is-shared=false
else
  sudo lpadmin -p POFF_RECEIPT -E -v "$URI" -m raw -o printer-is-shared=false
fi
if ! lpstat -p POFF_RECEIPT >/dev/null 2>&1; then
  echo ""
  echo "  ✗ 프린터 등록에 실패했어요. 위 메시지를 캡처해서 보내 주세요."
  read -k1 "?  아무 키나 누르면 닫혀요"; exit 1
fi
sudo cupsenable POFF_RECEIPT; sudo cupsaccept POFF_RECEIPT
echo ""
echo "  테스트 인쇄를 보내요..."
printf '\x1b@\x1ba\x01\x1d!\x11POFF\n\x1d!\x00PRINTER READY\n\n\x1bd\x04\x1dVB\x00' > /tmp/poff_test.bin
if ! lp -d POFF_RECEIPT -o raw /tmp/poff_test.bin; then
  echo "  ✗ 테스트 인쇄를 보내지 못했어요. 위 메시지를 캡처해서 보내 주세요."
  read -k1 "?  아무 키나 누르면 닫혀요"; exit 1
fi
echo ""
echo "  ✓ 등록 완료! 프린터에서 'POFF / PRINTER READY'가 나오면 성공이에요."
echo "    다음부터는 2_POFF_시작.command만 실행하면 돼요."
read -k1 "?  아무 키나 누르면 닫혀요"
