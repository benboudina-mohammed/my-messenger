import datetime
import hashlib
import sqlite3
import streamlit as st

# تهيئة قاعدة البيانات
conn = sqlite3.connect("chat.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    avatar TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    avatar TEXT,
    text TEXT,
    ts TEXT
)
""")
conn.commit()


def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


st.set_page_config(page_title="Messenger Pro", page_icon="💬")

# إدارة حالة الجلسة (Session State) لتسجيل الدخول
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["username"] = ""
  st.session_state["avatar"] = "😀"

if not st.session_state["logged_in"]:
  st.title("🔐 تسجيل الدخول / حساب جديد")
  tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])

  with tab1:
    l_user = st.text_input("اسم المستخدم", key="l_u")
    l_pass = st.text_input("كلمة المرور", type="password", key="l_p")
    if st.button("دخول"):
      p_hash = hash_password(l_pass)
      c.execute(
          "SELECT avatar FROM users WHERE username=? AND password_hash=?",
          (l_user, p_hash),
      )
      res = c.fetchone()
      if res:
        st.session_state["logged_in"] = True
        st.session_state["username"] = l_user
        st.session_state["avatar"] = res[0]
        st.rerun()
      else:
        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

  with tab2:
    r_user = st.text_input("اختر اسم مستخدم", key="r_u")
    r_pass = st.text_input("اختر كلمة مرور", type="password", key="r_p")
    r_avatar = st.selectbox(
        "اختر رمزك الشخصي (Avatar)", ["😀", "😎", "🦊", "🤖", "🐱", "🚀"]
    )
    if st.button("إنشاء الحساب"):
      try:
        p_hash = hash_password(r_pass)
        c.execute(
            "INSERT INTO users (username, password_hash, avatar) VALUES (?,?,"
            " ?)",
            (r_user, p_hash, r_avatar),
        )
        conn.commit()
        st.success("تم إنشاء الحساب! انتقل لتبويب تسجيل الدخول.")
      except sqlite3.IntegrityError:
        st.error("اسم المستخدمموجود مسبقاً، اختر غيره.")

else:
  # واجهة التطبيق بعد تسجيل الدخول
  with st.sidebar:
    st.write(f"الملف الشخصي: {st.session_state['avatar']}")
    st.subheader(f"مرحباً، {st.session_state['username']}")
    if st.button("تسجيل الخروج"):
      st.session_state["logged_in"] = False
      st.rerun()

    st.markdown("---")
    if st.button("🗑️ مسح سجل المحادثة"):
      c.execute("DELETE FROM messages")
      conn.commit()
      st.rerun()

  st.title("💬 ماسنجر الأصدقاء")

  # عرض الرسائل
  c.execute("SELECT id, user, avatar, text, ts FROM messages ORDER BY id ASC")
  for msg_id, u, av, txt, time in c.fetchall():
    is_me = u == st.session_state["username"]
    with st.chat_message("user" if is_me else "assistant"):
      st.markdown(f"{av} **{u}**: {txt}")
      st.caption(time)

  if prompt := st.chat_input("اكتب رسالتك واضغط Enter..."):
    current_time = datetime.datetime.now().strftime("%H:%M")
    c.execute(
        "INSERT INTO messages (user, avatar, text, ts) VALUES (?, ?, ?, ?)",
        (
            st.session_state["username"],
            st.session_state["avatar"],
            prompt,
            current_time,
        ),
    )
    conn.commit()
    st.rerun()
