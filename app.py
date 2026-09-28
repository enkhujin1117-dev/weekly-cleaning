import base64, io, json, os, random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st
from PIL import Image, ImageOps

TZ = ZoneInfo("Asia/Ulaanbaatar")
MAX_PHOTOS = 4  # нэг ажилд оруулах зургийн дээд тоо
PER = 4  # baristа bur 7 honogt avah tseverlgeenii too
DAYS = ["Даваа", "Мягмар", "Лхагва", "Пүрэв", "Баасан", "Бямба", "Ням"]
TASKS = ["Bar1 хөргөгч","Пос орчин","Бүх алчуур","Bar2 хөргөгч","Pantry эмх цэгц","Cake сав","Pantry хөргөгч","Pantry угаалтуур","Powder сав","Pantry хөлдөөгч","Pantry хар шүүгээ","Хогийн шүүр, тоглуур","Gelato хөлдөөгч","Gelato хар шүүгээ","Бохь түүх","Gelato зураг","Gelato пос орчин","Gelato угаалтуур","Menu board","Bene logo","Бүх сагс","Gelato show case","Шалны мод, хувин","Gelato шилэн хана","Cake show case","Номын тавиур","Төмөр хашлага","Gelato take гэрэл","Бүх сандал","Чулуун тавиан","Бүх ширээ","Selfbar","Бүх хогийн сав","Vip new york гэрэл","Take булан тохой","Pantry хана","Том цаг","Тонор төхөөрөмж","Булан тохой заал","Заал new york гэрэл","Take гэрэл","Жаазтай зураг","Take хар шүүгээ","Ногоон навч","Буйдан","Vip шилэн хана","Vip булан тохой","Chunks сав","1.2 давхарын шилэн хана","Бүх паар","Камер тавиур"]

# ---------------------------------------------------------------- storage
def _cfg():
    try:
        url = str(st.secrets["SUPABASE_URL"]).strip().strip('"').rstrip("/")
        if url.endswith("/rest/v1"):
            url = url[: -len("/rest/v1")]
        key = str(st.secrets["SUPABASE_KEY"]).strip()
        if not url.startswith("http"):
            st.error("SUPABASE_URL нь https:// гэж эхэлсэн байх ёстой (Secrets-ээ шалгана уу)")
            st.stop()
        return url, key
    except KeyError:
        return None, None

def _headers(key):
    h = {"apikey": key, "Content-Type": "application/json"}
    if not key.startswith("sb_"):  # шинэ sb_secret_... түлхүүр Authorization-д хэрэглэгддэггүй
        h["Authorization"] = f"Bearer {key}"
    return h

def _check(r):
    if not r.ok:
        st.error(f"Supabase алдаа {r.status_code}: {r.text[:300]}")
        st.stop()

LOCAL = "local_store.json"  # zuvhun computer deer turshihad (Cloud deer hadgalagdahgui)

@st.cache_data(ttl=10, show_spinner=False)
def load_all():
    url, key = _cfg()
    if url:
        r = requests.get(f"{url}/rest/v1/kv?select=key,value", headers=_headers(key), timeout=30)
        _check(r)
        return {x["key"]: x["value"] for x in r.json()}
    return json.load(open(LOCAL)) if os.path.exists(LOCAL) else {}

def put(k, v):
    url, key = _cfg()
    if url:
        h = _headers(key) | {"Prefer": "resolution=merge-duplicates"}
        _check(requests.post(f"{url}/rest/v1/kv", headers=h, json={"key": k, "value": v}, timeout=30))
    else:
        d = load_all().copy(); d[k] = v; json.dump(d, open(LOCAL, "w"))
    load_all.clear()

def delete(k):
    url, key = _cfg()
    if url:
        _check(requests.delete(f"{url}/rest/v1/kv", headers=_headers(key), params={"key": "eq." + k}, timeout=30))
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


THEMES = {  # нэр: (арын өнгө, карт, хажуу цэс, текст, гол өнгө)
    "🌸 Ягаан":     ("#f8e8ff", "#ffffff", "#efd3fb", "#3b2a4d", "#b455d6"),
    "☕ Кофе":      ("#f3e9dc", "#fffaf3", "#e6d3bd", "#3e2c1c", "#8b5a2b"),
    "🌿 Ногоон":    ("#e6f4ea", "#ffffff", "#cfe8d5", "#1e3a2a", "#2e9e5b"),
    "🌊 Цэнхэр":    ("#e3f0fb", "#ffffff", "#cde3f6", "#16324a", "#2b7cd3"),
    "🌙 Харанхуй":  ("#0e1117", "#1a1f2b", "#262730", "#f2f2f2", "#ff4b6e"),
}
DEFAULT_THEME = "🌸 Ягаан"

def apply_theme(name):
    bg, card, side, txt, acc = THEMES[name]
    st.markdown(f"""<style>
    .stApp {{ background: {bg}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{ background: {side}; }}
    .stApp, .stApp p, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3,
    .stApp li, [data-testid="stMarkdownContainer"] {{ color: {txt}; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ background: {card}; border-color: {acc}55; border-radius: 16px; }}
    .stButton > button, [data-testid="stPopover"] > button {{ background: {acc}; color: #fff; border: 0; border-radius: 10px; }}
    .stButton > button:hover {{ background: {acc}; color: #fff; opacity: .85; }}
    input, textarea, [data-baseweb="select"] > div {{ background: {card} !important; color: {txt} !important; }}
    [data-testid="stProgress"] div[data-baseweb="progress-bar"] > div > div {{ background: {acc} !important; }}
    </style>""", unsafe_allow_html=True)


def add_photos(key, imgs, at):
    n = st.session_state.get("uc" + key, 0)   # uploader-ийг дахин цэвэрлэх тоолуур
    files = st.file_uploader(f"📷 Зураг (дээд тал нь {MAX_PHOTOS})", type=["jpg", "jpeg", "png"],
                             accept_multiple_files=True, key=f"u{key}_{n}")
    if files:
        room = MAX_PHOTOS - len(imgs)
        new = imgs + [compress(f) for f in files[:room]]
        put(key, {"imgs": new, "at": at or int(datetime.now(TZ).timestamp())})
        st.session_state["uc" + key] = n + 1
        if len(files) > room:
            st.toast(f"Дээд тал нь {MAX_PHOTOS} зураг. Илүүг нь авсангүй.")
        st.rerun()

# ---------------------------------------------------------------- UI
st.set_page_config(page_title="Weekly Cleaning", page_icon="🧼", layout="wide")
st.title("🧼 Weekly Cleaning")

data = load_all()
state = data.get("state")
if state and state["weekStart"] < monday():   # 7 honog duussan -> automataar shine 7 honog
    rollover(state, data)
    data = load_all(); state = data["state"]

# --- admin (sidebar)
try:
    admin_pw = str(st.secrets["ADMIN_PASSWORD"]).strip()
except Exception:
    admin_pw = None
with st.sidebar:
    st.header("⚙️ Админ")
    if st.session_state.get("admin"):
        st.success("Админаар нэвтэрсэн")
        if st.button("Гарах"):
            st.session_state.admin = False; st.rerun()
    else:
        pw = st.text_input("Нууц үг", type="password")
        if st.button("Нэвтрэх"):
            if admin_pw and pw.strip() == admin_pw:
                st.session_state.admin = True; st.rerun()
            else:
                st.error("Буруу нууц үг (эсвэл ADMIN_PASSWORD тохируулаагүй)")
is_admin = st.session_state.get("admin", False)

# --- өнгөний сонголт (хүн бүр өөрийнхөөрөө, админ бүгдэд хадгалж болно)
saved = data.get("theme", {}).get("name", DEFAULT_THEME)
if "theme" not in st.session_state or st.session_state.theme not in THEMES:
    st.session_state.theme = saved if saved in THEMES else DEFAULT_THEME
with st.sidebar:
    st.divider()
    st.selectbox("🎨 Өнгө", list(THEMES), key="theme")
    if is_admin and st.button("🌐 Бүгдэд энэ өнгийг хадгалах"):
        put("theme", {"name": st.session_state.theme}); st.success("Хадгаллаа")
apply_theme(st.session_state.theme)

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
            imgs = ([rec["img"]] if "img" in rec else rec.get("imgs", [])) if rec else []
            can_edit = p == me_idx or is_admin
            if imgs:
                day = DAYS[datetime.fromtimestamp(rec["at"], TZ).weekday()]
                st.markdown(f"✅ **{t}**  \n:green[{day} гарагт хийсэн · {len(imgs)} зураг]")
                tc = st.columns(MAX_PHOTOS)
                for k, im in enumerate(imgs):
                    tc[k].image(base64.b64decode(im), use_container_width=True)
                if can_edit:
                    b1, b2 = st.columns(2)
                    with b1.popover("🗑 Устгах"):
                        opts = ["Бүх зураг"] + [f"Зураг {k + 1}" for k in range(len(imgs))]
                        pick = st.selectbox("Аль нь?", opts, key="s" + key)
                        if st.button("Тийм, устга", key="d" + key):
                            if pick == "Бүх зураг" or len(imgs) == 1:
                                delete(key)
                            else:
                                k = opts.index(pick) - 1
                                put(key, {"imgs": imgs[:k] + imgs[k + 1:], "at": rec["at"]})
                            st.rerun()
                    if len(imgs) < MAX_PHOTOS:
                        with b2.popover("➕ Зураг нэмэх"):
                            add_photos(key, imgs, rec["at"])
            else:
                st.markdown(f"⬜ **{t}**")
                if can_edit:
                    add_photos(key, [], None)

st.info("🧊 Цэвэрлэгээ бүрэн хийгээгүй хүмүүс мөсний машин, цагаан чулууг цэвэрлэнэ.")
