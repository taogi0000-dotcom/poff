# EPSON TM-T83II × 맥북 연결 가이드

POFF 영수증 스테이션 · 58mm 연두 감열지 · 인쇄 폭 48mm

## 준비물
- EPSON TM-T83II 영수증 프린터 + 전원 어댑터
- USB 케이블 (프린터 쪽은 네모난 USB-B)
- USB-C 젠더 또는 허브 — **데이터 전송이 되는 것** (충전 전용은 안 돼요)
- 58mm 감열지 (연두)
- `POFF_영수증스테이션` 폴더 (다운로드 폴더에 두기)

## 1. 프린터 연결
1. 용지를 넣고 덮개를 꽉 닫아요. 앞면 FEED 버튼을 눌러 종이가 나오면 OK.
2. 전원을 켜요.
3. 프린터 뒤 **USB-B 포트** → 젠더 → 맥북에 연결해요.
4. 맥북에 **"액세서리 연결을 허용하겠습니까?"** 가 뜨면 **허용**.
   - 안 뜨거나 거절했다면: 시스템 설정 → 개인정보 보호 및 보안 → "액세서리 연결 허용"을 **항상** 으로 바꾸고 USB를 다시 꽂아요.

## 2. 프린터 등록 (맥북마다 처음 한 번만)
1. `1_프린터_등록.command` 더블클릭.
   - "Apple은 … 확인할 수 없습니다" 경고가 뜨면: 시스템 설정 → 개인정보 보호 및 보안 → 아래쪽 **그래도 열기**.
2. 맥 비밀번호를 물어보면 입력 (화면에 안 보여도 정상).
3. 프린터에서 **POFF / PRINTER READY** 가 나오면 끝.

### 등록이 안 될 때 — 터미널에 직접 입력
```
sudo lpadmin -p POFF_RECEIPT -E -v "$(sudo lpinfo -v | awk '/usb:\/\/EPSON/{print $2; exit}')" -P "$(find /System/Library/Frameworks/ApplicationServices.framework -name Generic.ppd | head -1)" -o printer-is-shared=false
sudo cupsenable POFF_RECEIPT; sudo cupsaccept POFF_RECEIPT
printf '\x1b@\x1ba\x01\x1d!\x11POFF\n\x1d!\x00PRINTER READY\n\n\x1bd\x04\x1dVB\x00' > /tmp/poff_test.bin && lp -d POFF_RECEIPT -o raw /tmp/poff_test.bin
```
(최신 macOS는 예전 "raw" 등록 방식을 지원하지 않아서, Generic 드라이버로 등록하고 데이터만 그대로 보내요.)

## 3. 실행 (전시·발표할 때마다)
1. `2_POFF_시작.command` 더블클릭 → 창은 끝날 때까지 **닫지 않기**.
   - 처음이면 "명령어 라인 개발자 도구" 설치가 떠요 (10~30분, 한 번만).
2. 맥북 브라우저: **http://localhost:8080**
3. 아이패드: 창에 나온 **http://192.168.x.x:8080** (같은 와이파이)

### 테스트 주소
| 주소 | 용도 |
|---|---|
| `localhost:8080/test` | 프린터만 확인 (TEST PRINT OK) |
| `localhost:8080/#quick` | 질문 없이 영수증 두 장 바로 인쇄 · 키보드 **T** 로 반복 |
| `localhost:8080` | 실제 전체 흐름 (밀기 → 질문 3개 → 인쇄) |

## 4. 최신 키오스크로 업데이트
`2_POFF_시작` 창을 닫고 터미널에서:
```
curl -L -o ~/Downloads/POFF_영수증스테이션/kiosk.html https://raw.githubusercontent.com/taogi0000-dotcom/poff/main/station/kiosk.html
```
그다음 `2_POFF_시작.command` 다시 실행.

## 5. 문제 해결
| 증상 | 확인할 것 |
|---|---|
| "USB 프린터를 찾지 못했어요" | 전원 · USB-B 포트 · 데이터용 젠더 · 액세서리 허용 |
| 화면에 "프린터 연결을 확인해 주세요" | `2_POFF_시작` 창의 `FAILED` 메시지 확인 · `lpstat -p POFF_RECEIPT` |
| 인쇄 대기만 쌓이고 안 나옴 | `cancel -a POFF_RECEIPT` 후 프린터 전원 껐다 켜기 |
| "disabled / 사용 중지" | `sudo cupsenable POFF_RECEIPT` |
| 커팅이 안 됨 | 덮개를 열었다 꽉 닫고 전원 재시작 |
| 영수증이 한쪽으로 치우침 | 프린터 용지 폭 설정(58mm)·용지 가이드 위치 확인 |
| 아이패드에서 주소가 안 열림 | 같은 와이파이인지 · 맥 방화벽에서 python3 허용 |
| 장소를 옮김 | 맥 주소가 바뀌니 창에 새로 뜬 주소로 다시 열기 |
