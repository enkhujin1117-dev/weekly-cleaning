import base64, io, json, os, random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st
from PIL import Image, ImageOps

TZ = ZoneInfo("Asia/Ulaanbaatar")
PER = 4  # baristа bur 7 honogt avah tseverlgeenii too
DAYS = ["Даваа", "Мягмар", "Лхагва", "Пүрэв", "Баасан", "Бямба", "Ням"]
TASKS = ["Bar1 хөргөгч","Пос орчин","Бүх алчуур","Bar2 хөргөгч","Pantry эмх цэгц","Cake сав","Pantry хөргөгч","Pantry угаалтуур","Powder сав","Pantry хөлдөөгч","Pantry хар шүүгээ","Хогийн шүүр, тоглуур","Gelato хөлдөөгч","Gelato хар шүүгээ","Бохь түүх","Gelato зураг","Gelato пос орчин","Gelato угаалтуур","Menu board","Bene logo","Бүх сагс","Gelato show case","Шалны мод, хувин","Gelato шилэн хана","Cake show case","Номын тавиур","Төмөр хашлага","Gelato take гэрэл","Бүх сандал","Чулуун тавиан","Бүх ширээ","Selfbar","Бүх хогийн сав","Vip new york гэрэл","Take булан тохой","Pantry хана","Том цаг","Тонор төхөөрөмж","Булан тохой заал","Заал new york гэрэл","Take гэрэл","Жаазтай зураг","Take хар шүүгээ","Ногоон навч","Буйдан","Vip шилэн хана","Vip булан тохой","Chunks сав","1.2 давхарын шилэн хана","Бүх паар","Камер тавиур"]

# ---------------------------------------------------------------- storage
def _cfg():
    try:
        return st.secrets["SUPABASE_URL"].rstrip("/"), st.secrets["SUPABASE_KEY"]
    except Exception:
        return None, None

def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

LOCAL = "local_store.json"  # zuvhun computer deer turshihad (Cloud deer hadgalagdahgui)

@st.cache_data(ttl=10, show_spinner=False)
def load_all():
    url, key = _cfg()
    if url:
        r = requests.get(f"{url}/rest/v1/kv?select=key,value", headers=_headers(key), timeout=30)
        r.raise_for_status()
        return {x["key"]: x["value"] for x in r.json()}
    return json.load(open(LOCAL)) if os.path.exists(LOCAL) else {}

def put(k, v):
    url, key = _cfg()
    if url:
        h = _headers(key) | {"Prefer": "resolution=merge-duplicates"}
        requests.post(f"{url}/rest/v1/kv", headers=h, json={"key": k, "value": v}, timeout=30).raise_for_status()
    else:
        d = load_all().copy(); d[k] = v; json.dump(d, open(LOCAL, "w"))
    load_all.clear()

def delete(k):
    url, key = _cfg()
    if url:
        requests.delete(f"{url}/rest/v1/kv", headers=_headers(key), params={"key": "eq." + k}, timeout=30).raise_for_status()
    else:
        d = load_all().copy(); d.pop(k, None); json.dump(d, open(LOCAL, "w"))
    load_all.clear()

# ---------------------------------------------------------------- logic
def monday():
    d = datetime.now(TZ).date()
    return (d - timedelta(days=d.weekday())).isoformat()

def make_plan(n):
    pool = random.sample(TASKS, len(TASKS))
    return {str(p): pool[p * PER:(p + 1) * PER] for p in range(n)}

def did(w, p, i):
    return f"done:{w}_{p}_{i}"

def new_week(names, last_missed):
    w = monday()
    put("state", {"names": names, "weekStart": w, "plan": make_plan(len(names)), "lastMissed": last_missed})
    for k in [k for k in load_all() if k.startswith("done:") and not k.startswith(f"done:{w}_")]:
        delete(k)

def rollover(state, data):
    missed = []
    for p, n in enumerate(state["names"]):
        tasks = state["plan"].get(str(p), [])
        ok = sum(1 for i in range(len(tasks)) if did(state["weekStart"], p, i) in data)
        if ok < len(tasks):
            missed.append({"name": n, "done": ok, "total": len(tasks)})
    new_week(state["names"], {"week": state["weekStart"], "list": missed})

def compress(file):
    im = ImageOps.exif_transpose(Image.open(file)).convert("RGB")
    im.thumbnail((520, 520))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=55)
    return base64.b64encode(buf.getvalue()).decode()

# ---------------------------------------------------------------- UI
st.set_page_config(page_title="Weekly Cleaning", page_icon="🧼", layout="wide")
st.title("🧼 Weekly Cleaning")

data = load_all()
state = data.get("state")
if state and state["weekStart"] < monday():   # 7 honog duussan -> automataar shine 7 honog
    rollover(state, data)
    data = load_all(); state = data["state"]

# --- admin (sidebar)
admin_pw = st.secrets.get("ADMIN_PASSWORD", None) if hasattr(st, "secrets") else None
with st.sidebar:
    st.header("⚙️ Админ")
    if st.session_state.get("admin"):
        st.success("Админаар нэвтэрсэн")
        if st.button("Гарах"):
            st.session_state.admin = False; st.rerun()
    else:
        pw = st.text_input("Нууц үг", type="password")
        if st.button("Нэвтрэх"):
            if admin_pw and pw == admin_pw:
                st.session_state.admin = True; st.rerun()
            else:
                st.error("Буруу нууц үг (эсвэл ADMIN_PASSWORD тохируулаагүй)")
is_admin = st.session_state.get("admin", False)

if is_admin:
    with st.expander("Баристануудын жагсаалт / хуваарь гаргах", expanded=not state):
        txt = st.text_area("Мөр болгон нэг нэр", value="\n".join(state["names"]) if state else "")
        if st.button("🎲 Хуваарь гаргах"):
            names = list(dict.fromkeys(x.strip() for x in txt.splitlines() if x.strip()))
            if len(names) < 2:
                st.error("Дор хаяж 2 бариста оруулна уу")
            else:
                for k in [k for k in data if k.startswith("done:")]:
                    delete(k)
                new_week(names, state.get("lastMissed") if state else None)
                st.rerun()

if not state:
    st.info("Хуваарь хараахан гараагүй байна. Админ хуваарь гаргана.")
    st.stop()

w = state["weekStart"]
ws = datetime.fromisoformat(w); we = ws + timedelta(days=6)
st.caption(f"Энэ 7 хоног: {ws:%m/%d} – {we:%m/%d} · Ажлаа ямар ч өдөр хийж болно, Ням гарагт дуусгана")

lm = state.get("lastMissed")
if lm:
    if lm["list"]:
        lines = "  \n".join(f"**{x['name']}** — {x['done']}/{x['total']} хийсэн" for x in lm["list"])
        st.error(f"📋 Өнгөрсөн 7 хоног ({lm['week']}) — хийгээгүй хүмүүс  \n{lines}  \n→ Мөсний машин, цагаан чулуу цэвэрлэнэ")
    else:
        st.success(f"📋 Өнгөрсөн 7 хоног ({lm['week']}) — бүгд бүрэн хийсэн 🎉")

names = state["names"]
me = st.selectbox("Би хэн бэ?", ["— сонгох —"] + names, key="me")
me_idx = names.index(me) if me in names else None
order = sorted(range(len(names)), key=lambda p: p != me_idx)

cols = st.columns(3)
for n_i, p in enumerate(order):
    tasks = state["plan"].get(str(p), [])
    ok = sum(1 for i in range(len(tasks)) if did(w, p, i) in data)
    with cols[n_i % 3].container(border=True):
        badge = " ✅ Шалгагдсан" if tasks and ok == len(tasks) else ""
        st.subheader(f"{'👉 ' if p == me_idx else ''}{names[p]}{badge}")
        st.progress(ok / len(tasks) if tasks else 0.0, text=f"{ok}/{len(tasks)}")
        for i, t in enumerate(tasks):
            key = did(w, p, i); rec = data.get(key)
            if rec:
                day = DAYS[datetime.fromtimestamp(rec["at"], TZ).weekday()]
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"✅ **{t}**  \n:green[{day} гарагт хийсэн]")
                c2.image(base64.b64decode(rec["img"]), use_container_width=True)
                if is_admin and c1.button("🗑 Зураг устгах", key="d" + key):
                    delete(key); st.rerun()
            else:
                st.markdown(f"⬜ **{t}**")
                if p == me_idx or is_admin:
                    f = st.file_uploader("📷 Зураг", type=["jpg", "jpeg", "png"], key="u" + key)
                    if f:
                        put(key, {"img": compress(f), "at": int(datetime.now(TZ).timestamp())})
                        st.rerun()

st.info("🧊 Цэвэрлэгээ бүрэн хийгээгүй хүмүүс мөсний машин, цагаан чулууг цэвэрлэнэ.")
