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

# جدول الرسائل يدعم المرسل (sender) والمستقبل (receiver)
c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    avatar TEXT,
    text TEXT,
    ts TEXT
)
""")
conn.commit()


def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


st.set_page_config(page_title="Messenger Pro", page_icon="💬", layout="wide")

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["username"] = ""
  st.session_state["avatar"] = "😀"
  st.session_state["active_chat"] = None

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
      if not r_user or not r_pass:
        st.warning("يرجى ملء اسم المستخدم وكلمة المرور")
      else:
        try:
          p_hash = hash_password(r_pass)
          c.execute(
              "INSERT INTO users (username, password_hash, avatar) VALUES (?,?,"
              " ?)",
              (r_user, p_hash, r_avatar),
          )
          conn.commit()
          st.success("تم إنشاء الحساب بنجاح! انتقل لتبويب تسجيل الدخول.")
        except sqlite3.IntegrityError:
          st.error("اسم المستخدم موجود مسبقاً، اختر غيره.")

else:
  # واجهة التطبيق الرئيسية (خاصة)
  with st.sidebar:
    st.write(f"الملف الشخصي: {st.session_state['avatar']}")
    st.subheader(f"مرحباً، {st.session_state['username']}")
    if st.button("تسجيل الخروج"):
      st.session_state["logged_in"] = False
      st.session_state["active_chat"] = None
      st.rerun()

    st.markdown("---")
    st.subheader("🔍 بحث عن أصدقاء")
    search_query = st.text_input("ابحث باسم المستخدم...", "")

    st.subheader("👥 قائمة الأصدقاء")
    # جلب جميع المستخدمين ماعدا الحساب الحالي
    c.execute(
        "SELECT username, avatar FROM users WHERE username != ?",
        (st.session_state["username"],),
    )
    all_users = c.fetchall()

    # تصفية المستخدمين بناءً على خانة البحث
    filtered_users = [
        u
        for u in all_users
        if search_query.lower() in u[0].lower() or not search_query
    ]

    for friend_name, friend_avatar in filtered_users:
      if st.button(f"{friend_avatar} {friend_name}", key=f"chat_{friend_name}"):
        st.session_state["active_chat"] = friend_name
        st.rerun()

  # منطقة المحادثة الخاصة
  if st.session_state["active_chat"]:
    target_friend = st.session_state["active_chat"]
    st.title(f"💬 محادثة مع: {target_friend}")

    # جلب الرسائل الخاصة بين المستخدم الحالي والصديق المحدد
    c.execute(
        """
        SELECT sender, avatar, text, ts FROM messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY id ASC
    """,
        (
            st.session_state["username"],
            target_friend,
            target_friend,
            st.session_state["username"],
        ),
    )

    for sender_u, av, txt, time in c.fetchall():
      is_me = sender_u == st.session_state["username"]
      with st.chat_message("user" if is_me else "assistant"):
        st.markdown(f"{av} **{sender_u}**: {txt}")
        st.caption(time)

    if prompt := st.chat_input(f"اكتب رسالة إلى {target_friend}..."):
      current_time = datetime.datetime.now().strftime("%H:%M")
      c.execute(
          "INSERT INTO messages (sender, receiver, avatar, text, ts) VALUES"
          " (?, ?, ?, ?, ?)",
          (
              st.session_state["username"],
              target_friend,
              st.session_state["avatar"],
              prompt,
              current_time,
          ),
      )
      conn.commit()
      st.rerun()
  else:
    st.title("💬 ماسنجر الأصدقاء")
    st.info("👈 اختر صديقاً من القائمة الجانبية أو ابحث عنه لبدء محادثة خاصة.")
