# github.com/NoTinyxd
# for educational purposes only

import asyncio
import json
import re
import time
import sys
import signal
import threading
import requests
import base64
import io
import os
from PIL import Image, ImageDraw

_real_signal = signal.signal
def _safe_signal(sig, handler):
    if threading.current_thread() is threading.main_thread():
        return _real_signal(sig, handler)
signal.signal = _safe_signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curl_cffi.requests import Session
from console import log, gradient_token, overwrite, ts, R, WHITE, LABELS
from hsw import hsw
from motion import motion_data


def load_img(uri):
    if uri.startswith("data:"):
        data = uri.split(",", 1)[1]
        return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA")
    return Image.open(io.BytesIO(requests.get(uri).content)).convert("RGBA")


def img_size(uri):
    try:
        return load_img(uri).size
    except:
        return (547, 547)


def save_debug(cap, labeled, answers):
    os.makedirs("debug", exist_ok=True)
    rtype = labeled.get("type")
    task_map = {t["task_key"]: t for t in cap.get("tasklist", [])}

    for task_key, task in task_map.items():
        uri = task.get("datapoint_uri", "")
        if not uri:
            continue
        
        bg = load_img(uri)
        draw = ImageDraw.Draw(bg)
        iw, ih = bg.size

        if rtype == "area_select" and task_key in answers:
            pts = answers[task_key]
            x1, y1 = pts[0]
            x2, y2 = pts[1]
            if x1 == x2 and y1 == y2:
                draw.ellipse([x1 - 6, y1 - 6, x1 + 6, y1 + 6], fill="red", outline="white")
            else:
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            draw.text((x1 + 8, y1 - 8), f"{x1},{y1}", fill="red")

        elif rtype == "drag_drop" and task_key in answers:
            entity_map = {e["entity_id"]: e for e in task.get("entities", [])}
            for entry in answers[task_key]:
                eid = entry["entity_name"]
                ex, ey = entry["entity_coords"]
                entity = entity_map.get(eid, {})
                ew, eh = entity.get("size", [63, 63])
                entity_uri = entity.get("entity_uri", "")
                if entity_uri:
                    ent_img = load_img(entity_uri).resize((ew, eh))
                    bg.paste(ent_img, (ex - ew // 2, ey - eh // 2), ent_img)
                draw.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill="red", outline="white")
                draw.text((ex + 8, ey - 8), f"{ex},{ey}", fill="red")

        fname = f"debug/{task_key[:8]}_{int(time.time())}.png"
        bg.save(fname)
        print(f"debug image saved: {fname}")


class Nopecha:
    V1 = "https://api.nopecha.com/v1/recognition/hcaptcha"

    def __init__(self, key):
        self._auth = {"Authorization": f"Basic {key}"}

    def submit(self, cap):
        res = requests.post(self.V1, headers=self._auth, json={"data": cap}).json()
        if "data" not in res:
            raise Exception(f"nopecha submit failed: {res}")
        return res["data"]

    def poll(self, job_id, max_wait=120):
        deadline = time.time() + max_wait
        while time.time() < deadline:
            res = requests.get(self.V1, headers=self._auth, params={"id": job_id}).json()
            if "error" not in res:
                return res["data"]
            time.sleep(2)
        raise Exception(f"nopecha poll timeout")

    def label(self, cap):
        rtype = cap.get("request_type")
        results = self.poll(self.submit(cap))

        if rtype == "image_label_binary":
            tasklist = cap.get("tasklist", [])
            grid = results[0] if results else []
            answers = {t["task_key"]: grid[i] for i, t in enumerate(tasklist)}
            return {"type": "image_label_binary", "answers": answers}

        elif rtype in ("area_select", "image_label_area_select"):
            tasklist = cap.get("tasklist", [])
            answers = {}
            for i, task in enumerate(tasklist):
                row = results[i] if i < len(results) else {}
                box = row[0] if isinstance(row, list) else row
                iw, ih = img_size(task.get("datapoint_uri", ""))
                x1 = round(box["x"] / 100 * iw)
                y1 = round(box["y"] / 100 * ih)
                x2 = round((box["x"] + box["w"]) / 100 * iw) if box.get("w") else x1
                y2 = round((box["y"] + box["h"]) / 100 * ih) if box.get("h") else y1
                answers[task["task_key"]] = [[x1, y1], [x2, y2]]
            return {"type": "area_select", "answers": answers}

        elif rtype == "image_drag_drop":
            tasklist = cap.get("tasklist", [])
            answers = {}
            for i, task in enumerate(tasklist):
                task_results = results[i] if i < len(results) else []
                answers[task["task_key"]] = {
                    r["entity_id"]: {"x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"]}
                    for r in task_results
                }
            return {"type": "drag_drop", "answers": answers}

        raise Exception(f"unsupported challenge type: {rtype}")


def get_sec_ch_ua(ua):
    match = re.search(r"Chrome/(\d+)", ua)
    version = match.group(1) if match else "145"
    sec_ch_ua = f'"Google Chrome";v="{version}", "Chromium";v="{version}", "Not-A.Brand";v="24"'
    
    if "Windows" in ua:
        platform = "Windows"
    elif "Macintosh" in ua or "Mac OS" in ua:
        platform = "macOS"
    elif "Linux" in ua:
        platform = "Linux"
    else:
        platform = "Windows"
    
    return sec_ch_ua, platform


def make_session(proxy=None):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    sec_ch_ua, platform = get_sec_ch_ua(ua)
    
    s = Session(impersonate="chrome")
    s.headers.update({
        "user-agent": ua,
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "accept-encoding": "gzip, deflate, br, zstd",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": f'"{platform}"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
    })
    
    if proxy:
        s.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    
    return s, ua


def set_hcap_headers(s):
    s.headers.update({
        "origin": "https://newassets.hcaptcha.com",
        "referer": "https://newassets.hcaptcha.com/",
        "sec-fetch-site": "same-site",
    })


def set_site_headers(s, href):
    s.headers.update({
        "origin": href,
        "referer": f"{href}/",
        "sec-fetch-site": "cross-site",
    })


def get_version(s, href):
    set_site_headers(s, href)
    resp = s.get("https://js.hcaptcha.com/1/api.js")
    match = re.search(r"v1/([A-Za-z0-9]+)/static", resp.text)
    if not match:
        raise Exception("failed to extract hcaptcha version")
    return match.group(1)


def get_config(s, version, href, site, sitekey):
    set_site_headers(s, href)
    return s.post(
        "https://api2.hcaptcha.com/checksiteconfig",
        params={"v": version, "host": site, "sitekey": sitekey, "sc": "1", "swa": "1", "spst": "s"}
    ).json()


def get_captcha(s, version, site, sitekey, c_obj, n, motion, rqdata=None, lang="en-US"):
    set_hcap_headers(s)
    data = {
        "v": version,
        "sitekey": sitekey,
        "host": site,
        "hl": lang,
        "motionData": json.dumps(motion),
        "n": n,
        "c": json.dumps(c_obj),
    }
    if rqdata:
        data["rqdata"] = rqdata
    
    resp = s.post(
        f"https://api.hcaptcha.com/getcaptcha/{sitekey}",
        data=data,
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    try:
        return resp.json()
    except:
        raise Exception(f"getCaptcha error: {resp.status_code}")


def check_captcha(s, version, site, sitekey, cap, n, answers, motion, rqdata=None):
    set_hcap_headers(s)
    payload = {
        "v": version,
        "sitekey": sitekey,
        "serverdomain": site,
        "job_mode": cap.get("request_type", ""),
        "motionData": json.dumps(motion),
        "n": n,
        "c": json.dumps(cap["c"]),
        "answers": answers,
    }
    if rqdata:
        payload["rqdata"] = rqdata
    
    resp = s.post(
        f"https://api.hcaptcha.com/checkcaptcha/{sitekey}/{cap['key']}",
        data=json.dumps(payload),
        headers={"content-type": "application/json;charset=UTF-8"},
    )
    try:
        return resp.json()
    except:
        raise Exception(f"checkCaptcha error: {resp.status_code}")


async def solve_hsw(c_obj, ua, site, sitekey):
    log("SOLVING", "HSW PoW", "hsw")
    t0 = time.time()
    n = await hsw(c_obj.get("req", ""), site, sitekey)
    elapsed = round(time.time() - t0, 3)
    if not n:
        raise Exception("HSW solve failed")
    log("SUCCESS", f"hsw: {n[:48]}...", f"time: {elapsed}s")
    return n, elapsed


def build_ans(cap, labeled):
    rtype = labeled.get("type")
    if rtype in ("binary", "image_label_binary"):
        return labeled["answers"]
    elif rtype == "area_select":
        answers = {}
        for k, pts in labeled["answers"].items():
            if pts and isinstance(pts[0], (list, tuple)):
                answers[k] = pts
            else:
                answers[k] = [[p[0], p[1]] for p in pts]
        return answers
    elif rtype == "drag_drop":
        task_map = {t["task_key"]: t for t in cap.get("tasklist", [])}
        size_cache = {}
        answers = {}
        for task_key, entity_results in labeled["answers"].items():
            task = task_map.get(task_key, {})
            uri = task.get("datapoint_uri", "")
            if uri not in size_cache:
                size_cache[uri] = img_size(uri)
            iw, ih = size_cache[uri]
            print(f"image size for task {task_key[:8]}: {iw}x{ih}")
            entries = []
            for entity_id, pos in entity_results.items():
                x = round(pos["x"] / 100 * iw)
                y = round(pos["y"] / 100 * ih)
                entries.append({
                    "entity_name": entity_id,
                    "entity_type": "default",
                    "entity_coords": [x, y],
                })
            answers[task_key] = entries
        return answers
    return {}


def log_ent(cap):
    for task in cap.get("tasklist", []):
        for ent in task.get("entities", []):
            log("INFO", f"entity {ent['entity_id']} = coords: {ent['coords']} size: {ent['size']}")


async def solve(sitekey="4c672d35-0701-42b2-88c3-78380b0db560", site="discord.com", rqdata=None, proxy=None, nopecha_key="45yntv9awrevxkql"):
    href = f"https://{site}"
    s, ua = make_session(proxy)

    log("INFO", "fetching version")
    version = get_version(s, href)
    log("INFO", version, "version")

    log("INFO", "fetching site config")
    config = get_config(s, version, href, site, sitekey)
    if "c" not in config or "req" not in config["c"]:
        raise Exception("bad site config")

    c_obj = config["c"]
    md = motion_data(ua, href)
    motion = md.get_captcha()

    n, _ = await solve_hsw(c_obj, ua, site, sitekey)

    print(f"{ts()} {LABELS['PENDING']}PENDING{R} > {WHITE}getCaptcha{R}", flush=True)
    cap = get_captcha(s, version, site, sitekey, c_obj, n, motion, rqdata)
    overwrite(f"{ts()} {LABELS['INFO']}INFO{R} > {WHITE}getCaptcha received{R}")

    if cap.get("pass"):
        token = cap.get("generated_pass_UUID")
        if not token:
            raise Exception("silent pass but no token")
        log("CAPTCHA", gradient_token(token[:60]))
        return token

    challenge_type = cap.get("request_type", "unknown")
    task_count = len(cap.get("tasklist", []))
    entities = len(cap.get("tasklist", [{}])[0].get("entities", []))
    log("INFO", "got captcha", f"type: {challenge_type} | entities: {entities} | tasks: {task_count}")

    log_ent(cap)

    if not nopecha_key:
        raise Exception("nopecha_key required")

    log("SOLVING", "NopeCHA solving")
    labeled = Nopecha(nopecha_key).label(cap)
    log("SUCCESS", f"nopecha labeled {len(labeled.get('answers', {}))} tasks")

    answers = build_ans(cap, labeled)
    if not answers:
        raise Exception(f"build_answers failed for type: {labeled.get('type')}")

    print(f"answers: {json.dumps(answers, indent=2)}")
    save_debug(cap, labeled, answers)

    n2, _ = await solve_hsw(cap["c"], ua, site, sitekey)
    motion2 = md.check_captcha()

    print(f"{ts()} {LABELS['PENDING']}PENDING{R} > {WHITE}checkCaptcha{R}", flush=True)
    check = check_captcha(s, version, site, sitekey, cap, n2, answers, motion2, rqdata)
    overwrite(f"{ts()} {LABELS['INFO']}INFO{R} > {WHITE}checkCaptcha done{R}")

    log("INFO", f"checkCaptcha response: {check}")

    token = check.get("generated_pass_UUID")
    if not token:
        raise Exception("no token in response")
    log("SUCCESS", f"solved {token[:80]}")
    return token


if __name__ == "__main__":
    asyncio.run(solve(nopecha_key="45yntv9awrevxkql"))