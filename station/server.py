#!/usr/bin/env python3
# POFF RECEIPT station server for macOS
# - serves the kiosk to the iPad on the same Wi-Fi
# - receives each receipt (ESC/POS raster) and sends it to the USB receipt printer
import base64, json, os, socket, subprocess, sys, tempfile, datetime, time
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PRINTER = os.environ.get('POFF_PRINTER', 'POFF_RECEIPT')
PORT = int(os.environ.get('POFF_PORT', '8080'))
DRY = os.environ.get('POFF_DRYRUN') == '1'
HERE = os.path.dirname(os.path.abspath(__file__))
HTML = open(os.path.join(HERE, 'kiosk.html'), encoding='utf-8').read().replace('</head>', '<script>window.POFF_SERVER=1</script></head>', 1).encode('utf-8')
COUNT = 0

C_ENV = {**os.environ, 'LANG': 'C', 'LC_ALL': 'C'}   # English lpstat output, easy to parse

def run(cmd, t=8):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=t, env=C_ENV)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, str(e)

def printer_state():
    """('missing'|'disabled'|'ok', raw text)"""
    if DRY: return 'ok', 'dry-run'
    code, out = run(['lpstat', '-p', PRINTER])
    if code != 0 or not out: return 'missing', out
    if 'disabled' in out: return 'disabled', out
    return 'ok', out

def heal():
    """macOS pauses the queue after any USB/printer error and then silently holds new jobs. Turn it back on."""
    run(['cupsenable', PRINTER]); run(['cupsaccept', PRINTER])
    return printer_state()

def pending_jobs():
    code, out = run(['lpstat', '-o', PRINTER])
    return [l for l in out.splitlines() if l.strip()] if code == 0 else []

def send_raw(data: bytes):
    if DRY:
        p = os.path.join(HERE, 'last_print.bin'); open(p, 'wb').write(data); return True, 'dry-run saved'
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
        f.write(data); path = f.name
    try:
        st, info = printer_state()
        if st == 'disabled': st, info = heal()
        if st == 'missing': return False, '프린터가 등록돼 있지 않아요 · 1_프린터_등록.command 를 실행해 주세요'
        if st == 'disabled': return False, '프린터 대기열이 멈춰 있어요 · 터미널에서 sudo cupsenable ' + PRINTER
        code, out = run(['lp', '-d', PRINTER, '-o', 'raw', path], 20)
        if code != 0: return False, out
        # lp only means "queued". Make sure the printer actually took it.
        for _ in range(16):
            time.sleep(0.5)
            if printer_state()[0] == 'disabled':
                run(['cancel', '-a', PRINTER]); heal()
                return False, '프린터가 응답하지 않아요 · 전원 · USB · 용지 · 덮개를 확인해 주세요'
            if not pending_jobs(): return True, out
        return True, out + ' (아직 대기 중)'

    finally:
        try: os.unlink(path)
        except OSError: pass

def local_ip():
    for iface in ('en0', 'en1'):
        try:
            ip = subprocess.run(['ipconfig', 'getifaddr', iface], capture_output=True, text=True, timeout=3).stdout.strip()
            if ip: return ip
        except Exception: pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('10.255.255.255', 1)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception:
        return '127.0.0.1'

class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(body)
    def log_message(self, fmt, *args): pass
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html', '/kiosk'):
            return self._send(200, HTML, 'text/html; charset=utf-8')
        if path == '/test':
            data = b'\x1b@\x1ba\x01\x1d!\x11POFF\n\x1d!\x00TEST PRINT OK\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M').encode() + b'\n\x1bd\x04\x1dVB\x00'
            ok, msg = send_raw(data)
            return self._send(200 if ok else 500, json.dumps({'ok': ok, 'msg': msg}))
        if path == '/status':
            st, info = printer_state()
            if st == 'disabled': st, info = heal()
            return self._send(200, json.dumps({'ok': st == 'ok', 'state': st, 'printer': PRINTER, 'status': info, 'printed': COUNT}, ensure_ascii=False))
        self._send(404, json.dumps({'ok': False}))
    def do_POST(self):
        global COUNT
        if urlparse(self.path).path != '/print': return self._send(404, json.dumps({'ok': False}))
        try:
            n = int(self.headers.get('Content-Length', '0'))
            data = base64.b64decode(json.loads(self.rfile.read(n))['data'])
            ok, msg = send_raw(data)
            if ok: COUNT += 1
            print(f"[{datetime.datetime.now():%H:%M:%S}] receipt #{COUNT if ok else '-'} {'OK' if ok else 'FAILED: ' + msg}", flush=True)
            self._send(200 if ok else 500, json.dumps({'ok': ok, 'error': None if ok else msg}))
        except Exception as e:
            print('print error:', e, flush=True)
            self._send(500, json.dumps({'ok': False, 'error': str(e)}))

if __name__ == '__main__':
    ip = local_ip()
    print('=' * 52)
    print('  POFF RECEIPT 스테이션 실행 중')
    print(f'  아이패드 사파리에서 열기:  http://{ip}:{PORT}')
    print(f'  프린터 테스트:            http://{ip}:{PORT}/test')
    print('  끄려면 이 창에서 Control + C')
    st, info = heal() if not DRY else ('ok', 'dry-run')
    if st == 'ok' and not DRY: run(['cancel', '-a', PRINTER])   # drop jobs stuck from last time
    print({'ok': f'  ✓ 프린터 준비됨 ({PRINTER})', 'missing': '  ✗ 프린터가 등록돼 있지 않아요 → 1_프린터_등록.command 먼저 실행',
           'disabled': f'  ✗ 프린터 대기열이 멈춰 있어요 → 터미널: sudo cupsenable {PRINTER}'}[st])
    print('=' * 52, flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
