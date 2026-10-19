import hmac
import hashlib
import json
import base64
import requests
import urllib3
import concurrent.futures
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. إعدادات
# ═══════════════════════════════════════════════════════════
MAP_CODE = "9BE0030243BBCD52358071FEF732F4A51994"
REGION = "ME"
MAX_WORKERS = 30 # 30 حساب في نفس الوقت (أقصى شيء ممكن بدون حظر)

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

HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
KEY = bytes.fromhex(HEX_KEY)
AES_KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

# ═══════════════════════════════════════════════════════════
# 2. قائمة الحسابات (مضمنة داخل الكود)
# ═══════════════════════════════════════════════════════════
ACCOUNTS_RAW = """
H4XPCGNVFZC|H4XMJA4307B8-S1X_TEAM|4555603121|14841798073
H4XPCSB720A|H4XK1G7P610D-S1X_TEAM|4555603211|14841798536
H4XPCGV8DKL|H4XBTEDJWBP6-S1X_TEAM|4555603260|14841798902
H4XPCEK0PO9|H4XEX8DC30GE-S1X_TEAM|4555603323|14841799379
H4XPCDQV70P|H4XAW9O2SIRL-S1X_TEAM|4555603397|14841799826
H4XPCLNWKWL|H4XEAWZAURYQ-S1X_TEAM|4555603461|14841800218
H4XPCKSQLCH|H4XQJGKYOD6W-S1X_TEAM|4555603604|14841800615
S7lSXMPGD|S7LLXXT6UGOE-S1X_TEAM|4555611618|14841815543
S7lVLBVJQ|S7L8QUXNKDY8-S1X_TEAM|4555612051|14841816467
S7lAEMVWQ|S7LFDZ8ZEEMF-S1X_TEAM|4555612941|14841817207
S7l69TRM0|S7LYRBXKENCE-S1X_TEAM|4555613802|14841817513
S7lPMGYJO|S7LDK8QTXOX0-S1X_TEAM|4555613964|14841818423
S7lFKHEZ5|S7LZFLTWZ3J7-S1X_TEAM|4555614387|14841818784
S7lSO9QGF|S7LEZNRDKML8-S1X_TEAM|4555614764|14841819618
S7lTJMXBF|S7LHR6RDFK17-S1X_TEAM|4555614870|14841819948
S7lJJOQQC|S7LXPOMEKAEI-S1X_TEAM|4555614971|14841820309
S7lJL2PTJ|S7LJ2WHEYG3P-S1X_TEAM|4555615013|14841820640
S7lMVD8TJ|S7LUP4A85QZR-S1X_TEAM|4555625755|14841840544
S7l1KK9UI|S7LYQLRHGKY8-S1X_TEAM|4555625950|14841840930
S7lHUENB5|S7LEQABTL51X-S1X_TEAM|4555626124|14841841327
S7lQ1WNQN|S7LCHCUI22IQ-S1X_TEAM|4555626284|14841841661
S7lMYPUOT|S7LGUYGC5Z5H-S1X_TEAM|4555626414|14841842023
S7lFP1HJS|S7LG79GTDB4A-S1X_TEAM|4555626580|14841842357
S7lZ9VD0T|S7LR8I2JSA3B-S1X_TEAM|4555626858|14841842993
S7lA9MNQD|S7LSOD3DWSDH-S1X_TEAM|4555626925|14841843417
S7lFZ2GCW|S7L2R4WFRI5K-S1X_TEAM|4555626978|14841844841
S7l1ZDEKJ|S7LGIIOKVQXD-S1X_TEAM|4555629318|14841845837
S7lWTKMA6|S7LROQKCQWWW-S1X_TEAM|4555629643|14841847147
S7lTCS8BK|S7LT5555B7VZ-S1X_TEAM|4555629698|14841847460
S7lYCCUJX|S7L432EGSDTQ-S1X_TEAM|4555629769|14841847767
S7lTCWIXE|S7L8VMQJFCAY-S1X_TEAM|4555629853|14841848202
S7lG66DR4|S7LRNC59NLFO-S1X_TEAM|4555630041|14841849100
S7lOYGX62|S7LDO092IQHZ-S1X_TEAM|4555630092|14841849437
S7lST4EPV|S7LIBUAQMKIF-S1X_TEAM|4555630883|14841849841
S7lFJUQLV|S7LS6V9T1BOP-S1X_TEAM|4555631918|14841850277
S7l168MPB|S7LKFJ8EWQTE-S1X_TEAM|4555632289|14841850714
S7l3VI3J3|S7LRPTVFY61P-S1X_TEAM|4555632916|14841853724
S7lXZASH9|S7LWOJ68GAHY-S1X_TEAM|4555633110|14841854121
S7lL0TU42|S7LBPLQSWOIE-S1X_TEAM|4555633862|14841855538
S7LFZECD2|S7LDKJEZ6I12-S1X_TEAM|4555719862|14842006349
S7LYIZAC1|S7LLLYSK70YR-S1X_TEAM|4555720054|14842006896
S7LQ57WA5|S7LBW8CPZYGK-S1X_TEAM|4555720196|14842007319
S7LBTMSJT|S7LXBIREJV4Z-S1X_TEAM|4555720320|14842007712
S7LP1YZUE|S7LSBIQKNRWB-S1X_TEAM|4555720526|14842008192
S7LYKEBGQ|S7LXN1W9JZYC-S1X_TEAM|4555720745|14842008622
S7LRILLS2|S7L4TR5HF11C-S1X_TEAM|4555720853|14842009073
S7LID3OPM|S7LPAHS9NU82-S1X_TEAM|4556615537|14843683723
S7LN4BHCB|S7LVFV4GPKRB-S1X_TEAM|4556615620|14843684137
S7LKI87S5|S7LHXQXDKFMG-S1X_TEAM|4556615700|14843684509
S7LOVNBH0|S7LRB1WFIPQC-S1X_TEAM|4556615992|14843685418
S7L3VW64Y|S7LJFPJVDZHZ-S1X_TEAM|4556616059|14843685779
S7LZRVJCT|S7LRTTSMMWJA-S1X_TEAM|4556616132|14843686137
S7LDQRGHE|S7LYKHVUMTBG-S1X_TEAM|4556616203|14843686462
S7LIJLFJE|S7L5ECXOVAVD-S1X_TEAM|4556616278|14843686800
S7LJ98FLA|S7LUHFJEQXAK-S1X_TEAM|4556616363|14843687190
S7LF8W5PH|S7LIASVXGD6V-S1X_TEAM|4556616453|14843687582
S7LEVZVAN|S7LJ8Y0A026N-S1X_TEAM|4556616638|14843688600
S7LQTWAHQ|S7LU478JQBY3-S1X_TEAM|4556616730|14843689150
S7L1GLUJL|S7LUQCTE5EGO-S1X_TEAM|4556616834|14843689642
S7L6ZIIXH|S7LENS9OZTMY-S1X_TEAM|4556616957|14843690211
S7LQEBWKT|S7LLFQRRJVXC-S1X_TEAM|4556617098|14843690721
S7LBHXSIT|S7LF936MSJXR-S1X_TEAM|4556617214|14843691103
S7LMELTHX|S7LGGVVKN7KJ-S1X_TEAM|4556617302|14843691584
S7LBBYQNP|S7LVXYZP4KKK-S1X_TEAM|4556617415|14843692134
S7L3BPS5H|S7LOOJ2OSS0N-S1X_TEAM|4556617491|14843692572
S7LYHS0VL|S7LFEPHKOOD5-S1X_TEAM|4556617569|14843693036
S7LJJCEBG|S7LLI53DJS4H-S1X_TEAM|4556617663|14843693429
S7LGNTAVU|S7LWHKTK4AT4-S1X_TEAM|4556617747|14843693949
S7L9CQMFU|S7L0BQW2SU0X-S1X_TEAM|4556617848|14843694373
S7L8EISYP|S7L53PSOYW1S-S1X_TEAM|4556617917|14843694821
S7L4UFF8Q|S7LXNL4QNUNH-S1X_TEAM|4556617982|14843695221
S7LEU5YMJ|S7LTY54YUAZ2-S1X_TEAM|4556618108|14843695780
S7L0WCWSV|S7LO0TWRMC0B-S1X_TEAM|4556618270|14843696182
S7LCSPFTG|S7L1AT8VV05L-S1X_TEAM|4556618530|14843697242
S7LEUEIMN|S7LKGDYQQCNY-S1X_TEAM|4556618619|14843697641
S7LRP52YP|S7LS67JTBCEG-S1X_TEAM|4556618696|14843698099
S7LYKPLFX|S7L3LCD0JRLO-S1X_TEAM|4556618793|14843698570
S7LAATDID|S7LDD1LYABUS-S1X_TEAM|4556618873|14843698951
S7LYXPPUT|S7L1THS8JL0A-S1X_TEAM|4556619046|14843699876
S7LYDCEPM|S7LD5EXTUVEB-S1X_TEAM|4556619227|14843700795
S7LRUIUMY|S7LJOK6FG2G4-S1X_TEAM|4556619521|14843701800
S7LBKFOFM|S7L4IPW7VPIK-S1X_TEAM|4556619713|14843702735
S7LNWJRFW|S7LNUQTQIHXB-S1X_TEAM|4556619886|14843703543
S7L2E1AQU|S7LDEC8IZ2ZN-S1X_TEAM|4556620078|14843704564
S7LYTIDNA|S7LU4ANGICCC-S1X_TEAM|4556620242|14843705384
S7L2Y66QL|S7LJXJHO7GAL-S1X_TEAM|4556620339|14843705791
S7L7T8YZR|S7LZWJHDP87N-S1X_TEAM|4556620465|14843706256
S7L6XO1QR|S7LVE0SNULN7-S1X_TEAM|4556620628|14843706688
S7LMYD4HC|S7LMYZX5T8PN-S1X_TEAM|4556620827|14843707612
S7LJGAQ5P|S7LSTGT0W2FC-S1X_TEAM|4556620938|14843708021
S7LTH1A7E|S7LER1NO1DZV-S1X_TEAM|4556621023|14843708340
S7LVTLASZ|S7LDEVR90TK0-S1X_TEAM|4556621217|14843709266
S7LNOT5XX|S7LG16WVVPEX-S1X_TEAM|4556621305|14843709646
S7LQFBZAV|S7L2LLJ7CDXN-S1X_TEAM|4556621393|14843710061
S7LMDBW6M|S7LBZVOMQGLD-S1X_TEAM|4556621575|14843711046
S7LY69MU1|S7LVDMQ0W4XT-S1X_TEAM|4556621858|14843712146
S7L2JINX9|S7LSA7RCOQWX-S1X_TEAM|4556622080|14843713095
S7LV5JUCG|S7LMJVS3RPX4-S1X_TEAM|4556622274|14843714104
S7LQG8YHU|S7LDFONYFONV-S1X_TEAM|4556622373|14843714723
S7LN9MVTH|S7LPEWRHCHID-S1X_TEAM|4556622464|14843715199
S7L7QMPH4|S7LDSTSZIZB5-S1X_TEAM|4556622534|14843715549
S7LLBVSHP|S7LERBB1QC5T-S1X_TEAM|4556622607|14843715986
S7L0W48LB|S7LFLVZPYEQX-S1X_TEAM|4556622688|14843716468
S7LDCK1UB|S7LYEB7QD2GO-S1X_TEAM|4556622781|14843716894
S7LBK36PF|S7LKQRN2ASL4-S1X_TEAM|4556623075|14843717976
S7LZRZSAY|S7LREQHLGKZN-S1X_TEAM|4556623267|14843718900
S7LAMUSWQ|S7LJOTP8NIZE-S1X_TEAM|4556623375|14843719340
S7LSV57KX|S7LBNZEXOL9L-S1X_TEAM|4556623467|14843719774
S7LV9BPGB|S7LJCVP53Y8C-S1X_TEAM|4556623543|14843720232
S7LJSFKNT|S7LM7ZFSFWCZ-S1X_TEAM|4556623639|14843720663
S7LCZXSLJ|S7LJOHHYPRIR-S1X_TEAM|4556623766|14843721460
S7LA8X8RD|S7LQH3OEUPI7-S1X_TEAM|4556623883|14843722021
S7LJ1Z4HM|S7LUVHAWLI7L-S1X_TEAM|4556623992|14843722616
S7LKKW5BL|S7LNEY4SHV5K-S1X_TEAM|4556624135|14843723138
S7LZEJ0CM|S7LDAFUL4AXK-S1X_TEAM|4556624258|14843723523
S7LJ4QWIL|S7L9OR6KCB8G-S1X_TEAM|4556624361|14843723985
S7LB0EQUQ|S7LPU0LPV3LN-S1X_TEAM|4556624483|14843724645
S7LYPPT1W|S7LD6YX3ZGQN-S1X_TEAM|4556624586|14843725074
S7LXPHUCB|S7LB8UNTTEDQ-S1X_TEAM|4556624695|14843725601
S7LUZSZK4|S7L0CUUX310F-S1X_TEAM|4556624760|14843725996
S7LWAZNTL|S7LDHUW3FEIZ-S1X_TEAM|4556624854|14843726479
S7L0YWYM9|S7LPRSIK5SNW-S1X_TEAM|4556624928|14843726832
S7LPD1KOK|S7LP6DISUSET-S1X_TEAM|4556625007|14843727213
S7LYPO0VK|S7LFERTAKWWC-S1X_TEAM|4556625120|14843727788
S7LGMI3PZ|S7LF6PG8Q3OL-S1X_TEAM|4556625278|14843728449
S7LYENBAK|S7LSZO5WOFEI-S1X_TEAM|4556625414|14843728969
S7LDUSMTX|S7LIZL4WS0G5-S1X_TEAM|4556625511|14843729320
S7LXF2Q5O|S7L3TYQ00EYL-S1X_TEAM|4556625607|14843729786
S7LBGWVC8|S7LFCQY6WN1H-S1X_TEAM|4556625685|14843730335
S7LGQN0YF|S7LL51LU2MEG-S1X_TEAM|4556625781|14843730852
S7LWCE424|S7LS5GCNZC9L-S1X_TEAM|4556625895|14843731460
S7LT8ED2G|S7LEFGEFO4NF-S1X_TEAM|4556625979|14843731848
S7LN0YHFG|S7L2GDZSOBDE-S1X_TEAM|4556626058|14843732220
S7LAIMDTB|S7LRLU7QFRUR-S1X_TEAM|4556626144|14843732623
S7LXSP9RO|S7LO2C3FZMYK-S1X_TEAM|4556626243|14843732979
S7LZQ0J8J|S7LSR5DAVVHE-S1X_TEAM|4556626368|14843733441
S7LRVPGOG|S7LCOBPUKZWZ-S1X_TEAM|4556626471|14843733950
S7LSJPZZW|S7LJAKS7YQUV-S1X_TEAM|4556626630|14843734584
S7L3UDWLM|S7LCFSKN3DMJ-S1X_TEAM|4556626750|14843735232
S7LNW2AY1|S7LX7S8FD44K-S1X_TEAM|4556626871|14843735821
S7LLBC5XS|S7LIPJ5KBKRC-S1X_TEAM|4556626959|14843736357
S7LYWSDA6|S7L9RZYLFZHE-S1X_TEAM|4556627058|14843736813
S7LBN9LDR|S7LTCZK6RWCW-S1X_TEAM|4556627131|14843737161
S7LLVPVRP|S7LSHZT3Y4A1-S1X_TEAM|4556627218|14843737716
S7LY2F4PM|S7LR4ORUMAI5-S1X_TEAM|4556627294|14843738103
S7LXYWRG2|S7LEJ1RI0NA6-S1X_TEAM|4556627408|14843738663
S7L3DUVQP|S7LNS768PLPJ-S1X_TEAM|4556627552|14843739262
S7LMNZMJC|S7LWVWB7KD0N-S1X_TEAM|4556627681|14843739803
S7LKVEDIH|S7LVMQVQO77L-S1X_TEAM|4556627775|14843740227
S7LUCLKI1|S7LBAONCOOUN-S1X_TEAM|4556627859|14843741387
S7LCYDHVS|S7LMHYNJJESF-S1X_TEAM|4556628115|14843741828
"""

def parse_accounts(raw):
    accounts = []
    for line in raw.strip().splitlines():
        parts = line.strip().split('|')
        if len(parts) >= 3:
            password = parts[1]
            uid = parts[2]
            accounts.append({"uid": uid, "password": password})
    return accounts

ACCOUNTS = parse_accounts(ACCOUNTS_RAW)

# ═══════════════════════════════════════════════════════════
# 3. دوال التشفير والـ API
# ═══════════════════════════════════════════════════════════
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
        raise Exception(f"login_{j.get('code')}")
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
        raise Exception("major_failed")

    jstart = r.text.find("eyJ")
    if jstart == -1:
        raise Exception("jwt_missing")
    jwt = r.text[jstart:]
    second_dot = jwt.find(".", jwt.find(".") + 1)
    if second_dot == -1:
        raise Exception("jwt_malformed")
    return jwt[:second_dot + 44]

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

def process_account(acc):
    uid = acc["uid"]
    password = acc["password"]
    region_url = REGION_URLS.get(REGION, REGION_URLS["BD"])
    
    session = requests.Session()
    try:
        open_id, access_token = get_token(uid, password, session)
        jwt = major_login(access_token, open_id, session)
        ok = subscribe_workshop(jwt, MAP_CODE, region_url, session)
        return (uid, True if ok else False, "ok" if ok else "rejected")
    except Exception as e:
        return (uid, False, str(e))
    finally:
        session.close()

# ═══════════════════════════════════════════════════════════
# 4. Endpoint Vercel
# ═══════════════════════════════════════════════════════════
@app.get("/")
def root():
    return {"status": "alive", "message": "Go to /trigger to start"}

@app.get("/trigger")
def trigger():
    start_time = time.time()
    results = []
    
    # استخدام 30 Threads لتسريع العملية (كلما زاد الرقم، كلما انتهى أسرع، لكنه قد يسبب حظر IP)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_account, acc) for acc in ACCOUNTS]
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append(("unknown", False, str(e)))

    elapsed = time.time() - start_time
    successes = [r for r in results if r[1]]
    failures = [r for r in results if not r[1]]

    return JSONResponse({
        "status": "completed",
        "total": len(ACCOUNTS),
        "success_count": len(successes),
        "fail_count": len(failures),
        "time_taken_seconds": round(elapsed, 2),
        "successes": [{"uid": s[0]} for s in successes],
        "failures": [{"uid": f[0], "error": f[2]} for f in failures]
    })
