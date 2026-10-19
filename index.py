import hmac
import hashlib
import json
import base64
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Craftland Subscriber")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)

HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
KEY = bytes.fromhex(HEX_KEY)
AES_KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

REGION_URLS = {
    "IND": "https://client.ind.freefiremobile.com/",
    "BR":  "https://client.us.freefiremobile.com/",
    "SAC": "https://client.us.freefiremobile.com/",
    "ID":  "https://clientbp.ggpolarbear.com/",
    "ME":  "https://clientbp.ggpolarbear.com/",
    "VN":  "https://clientbp.ggpolarbear.com/",
    "TH":  "https://clientbp.ggpolarbear.com/",
    "BD":  "https://clientbp.ggpolarbear.com/",
    "PK":  "https://clientbp.ggpolarbear.com/",
    "SG":  "https://clientbp.ggpolarbear.com/",
    "TW":  "https://clientbp.ggpolarbear.com/",
}

HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Craftland Subscriber</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0a0a12;color:#eee;min-height:100vh;
    font-family:system-ui,-apple-system,sans-serif;
    display:flex;align-items:center;justify-content:center;padding:20px}
  .card{background:#14141e;border:1px solid #25253a;
    border-radius:16px;padding:32px;max-width:480px;width:100%}
  h1{font-size:22px;margin-bottom:8px;color:#8b5cf6}
  p{color:#888 except;font-size:13px;margin-bottom:24px}
  label{display:block;font-size:12px;color:#aaa; HTTPmargin:16px 0 6pxException}
  input{width:100%;background:#0:
a0a12;border:1px solid        #25253a;
    border-radius: raise10px;padding:12px 14px;color:#eee;
    font-family:inherit;font-size:14px;outline:none}
  input:focus{border-color:#8b5cf6}
  button{width:100%;margin-top:24px;padding:14px;
    background:linear-gradient(135deg,#8b5cf6,#ec4899);
    border:none;border-radius:10px;color:#fff;
    font-weight:700;font-size:14px;cursor:pointer}
  button:disabled{opacity:.5;cursor:not-allowed}
  .result{margin-top:20px;padding:14px;border-radius:10px;
    font-size:13px;line-height:1.7}
  .result.ok{background:rgba(16,240,152,.1);border:1px solid #10f098;color:#10f098}
  .result.err{background:rgba(244,63,94,.1);border:1px solid #f43f5e;color:#f43f5e}
  .result.warn{background:rgba(245,184,0,.1);border:1px solid #f5b800;color:#f5b800}
</style>
</head>
<body>
<div class="card">
  <h1>🎮 Craftland Subscriber</h1>
  <p>أدخل بيانات حسابك + كود الخريطة</p>
  <label>UID (رقم الحساب)</label>
  <input id="uid" placeholder="123456789" autocomplete="off">
  <label>كلمة السر</label>
  <input id="password" type="password" placeholder="••••••••">
  <label>كود الخريطة</label>
  <input id="map_code" placeholder="12345678" autocomplete="off">
  <label>المنطقة</label>
  <input id="region" value="BD" placeholder="BD / ME / ID / IND / BR">
  <button id="btn" onclick="run()">🚀 اشترك</button>
  <div id="out"></div>
</div>
<script>
async function run(){
  const btn=document.getElementById('btn'),out=document.getElementById('out');
  const data={
    uid:document.getElementById('uid').value.trim(),
    password:document.getElementById('password').value,
    map_code:document.getElementById('map_code').value.trim(),
    region:document.getElementById('region').value.trim()||'BD',
  };
  if(!data.uid||!data.password||!data.map_code){
    out.className='result warn';out.textContent='⚠️ عبّئ كل الحقول';return;
  }
  btn.disabled=true;btn.textContent='⏳ جاري...';out.className='';out.textContent='';
  try{
    const r=await fetch('/api/subscribe',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data),
    });
    const j=await r.json();
    if(r.ok&&j.success){
      out.className='result ok';
      out.innerHTML=`✅ تم الاشتراك<br>UID: <b>${j.uid}</b><br>Account ID: <b>${j.account_id}</b><br>Map: <b>${j.map_code}</b>`;
    }else{
      out.className='result err';
      out.textContent='❌ '+(j.detail||j.message||'فشل');
    }
  }catch(e){
    out.className='result err';out.textContent='❌ '+e.message;
  }finally{
    btn.disabled=false;btn.textContent='🚀 اشترك';
  }
}
</script>
</body>
</html>"""

def encode_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n: b |= 0x80
        out.append(b)
        if not n: break
    return bytes(out)

def create_proto(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested = create_proto(value)
            packet.extend(encode_varint((field << 3) | 2))
            packet.extend(encode_varint(len(nested)))
            packet.extend(nested)
        elif isinstance(value, int):
            packet.extend(encode_varint((field << 3) | 0))
            packet.extend(encode_varint(value))
        elif isinstance(value, (str, bytes)):
            enc = value.encode() if isinstance(value, str) else value
            packet.extend(encode_varint((field << 3) | 2))
            packet.extend(encode_varint(len(enc)))
            packet.extend(enc)
    return bytes(packet)

def aes_encrypt(data_bytes):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(data_bytes, 16))

def get_token(uid, password, session):
    url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    payload = {
        "client_id": 100067,
        "client_secret": HEX_KEY,
        "client_type": 2,
        "password": password,
        "response_type": "token",
        "uid": uid,
    }
    body = json.dumps(payload, separators=(',', ':'))
    sig = hmac.new(KEY, body.encode(), hashlib.sha256).hexdigest()
    headers = {
        "User-Agent": "GarenaMSDK/4.0.39(SM-A325M ;Android 13;en;HK;)",
        "Authorization": f"Signature {sig}",
        "Content-Type": "application/json; charset=utf-8",
    }
    r = session.post(url, headers=headers, data=body, verify=False, timeout=15)
    j = r.json()
    if j.get("code") != 0:
        raise HTTPException(400, f"login_failed_{j.get('code')}")
    return j["data"]["open_id"], j["data"]["access_token"]

def major_login(access_token, open_id, session):
    payload = (
        b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02'
        b'en'
        b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
    )
    payload = payload.replace(
        b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390',
        access_token.encode()
    ).replace(
        b'1d8ec0240ede109973f3321b9354b44d',
        open_id.encode()
    )
    encrypted = aes_encrypt(payload)

    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    headers = {
        "Accept-Encoding": "gzip",
        "Authorization": "Bearer",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue",
        "ReleaseVersion": "OB54",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
        "X-GA": "v1 1",
        "X-Unity-Version": "2018.4.11f1",
    }
    r = session.post(url, headers=headers, data=encrypted, verify=False, timeout=20)
    if r.status_code != 200 or len(r.text) < 10:
        raise HTTPException(502, "major_login_failed")

    jstart = r.text.find("eyJ")
    if jstart == -1:
        raise HTTPException(502, "jwt_not_found")
    jwt = r.text[jstart:]
    second_dot = jwt.find(".", jwt.find(".") + 1)
    if second_dot == -1:
        raise HTTPException(502, "jwt_malformed")
    jwt = jwt[:second_dot + 44]

    try:
        parts = jwt.split('.')
        padded = parts[1] + '=' * ((4 - len(parts[1]) % 4) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        account_id = str(decoded.get('account_id') or decoded.get('external_id', 'N/A'))
    except Exception:
        account_id = "N/A"

    return jwt, account_id

def subscribe_workshop(jwt, code, region_url, session):
    endpoint = region_url.rstrip('/') + "/SubscribeWorkshopCode"
    proto = create_proto({1: 1, 2: code, 3: 26, 4: "en"})
    encrypted = AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(proto, 16))
    headers = {
        "User-Agent": "UnityPlayer/2022.3.47f1",
        "Authorization": f"Bearer {jwt}",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB54",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2022.3.47f1",
    }
    r = session.post(endpoint, headers=headers, data=encrypted, verify=False, timeout=20)
    return r.status_code == 200

class SubscribeInput(BaseModel):
    uid: str
    password: str
    map_code: str
    region: str = "BD"

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE

@app.get("/api/health")
def health():
    return {"ok": True, "service": "craftland-subscriber"}

@app.post("/api/subscribe")
async def subscribe_route(data: SubscribeInput):
    region = data.region.upper()
    if region not in REGION_URLS:
        region = "BD"
    region_url = REGION_URLS[region]

    code = data.map_code.strip()
    if code.lower().startswith("#freefire"):
        code = code[9:]
    elif code.startswith("#"):
        code = code[1:]
    code = code.strip()
    if not code:
        raise HTTPException(400, "map_code_required")

    session = requests.Session()
    try:
        open_id, access_token = get_token(data.uid, data.password, session)
        jwt, account_id = major_login(access_token, open_id, session)
        ok = subscribe_workshop(jwt, code, region_url, session)
        return {
            "success": ok,
            "uid": data.uid,
            "account_id": account_id,
            "map_code": code,
            "region": region,
            "message": "subscribed" if ok else "subscribe_rejected",
        }
   
    except Exception as e:
        raise HTTPException(500, f"error: {str(e)}")
    finally:
        session.close()