import datetime
import hashlib
import sqlite3
import streamlit as st

# تهيئة قاعدة البيانات الآمنة
conn = sqlite3.connect("chat.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    avatar TEXT,
    bio TEXT DEFAULT 'مرحباً، أنا أستخدم ماسنجر الأصدقاء!',
    status TEXT DEFAULT 'online'
)
""")

for col, def_val in [
    ("bio", "'مرحباً، أنا أستخدم ماسنجر الأصدقاء!'"),
    ("status", "'online'"),
]:
  try:
    c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {def_val}")
    conn.commit()
  except sqlite3.OperationalError:
    pass

c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    avatar TEXT,
    text TEXT,
    ts TEXT,
    is_read INTEGER DEFAULT 0
)
""")
conn.commit()


def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


st.set_page_config(page_title="Messenger Pro", page_icon="💬", layout="wide")

st.markdown("""

""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["username"] = ""
  st.session_state["avatar"] = "😀"
  st.session_state["bio"] = ""
  st.session_state["status"] = "online"
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
          "SELECT avatar, bio, status FROM users WHERE username=? AND"
          " password_hash=?",
          (l_user, p_hash),
      )
      res = c.fetchone()
      if res:
        st.session_state["logged_in"] = True
        st.session_state["username"] = l_user
        st.session_state["avatar"] = res if len(res) > 0 else "😀"
        st.session_state["bio"] = (
            res if len(res) > 1 and res else "مرحباً!"
        )
        st.session_state["status"] = (
            res if len(res) > 2 and res else "online"
        )
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
              "INSERT INTO users (username, password_hash, avatar, bio,"
              " status) VALUES (?,?,?,?,?)",
              (
                  r_user,
                  p_hash,
                  r_avatar,
                  "مرحباً، أنا أستخدم ماسنجر الأصدقاء!",
                  "online",
              ),
          )
          conn.commit()
          st.success("تم إنشاء الحساب بنجاح! انتقل لتبويب تسجيل الدخول.")
        except sqlite3.IntegrityError:
          st.error("اسم المستخدم موجود مسبقاً، اختر غيره.")

else:
  # مزامنة الحالة فقط إذا كان المستخدم مسجلاً بشكل صحيح
  if st.session_state.get("username"):
    c.execute(
        "UPDATE users SET status=? WHERE username=?",
        (
            st.session_state.get("status", "online"),
            st.session_state["username"],
        ),
    )
    conn.commit()

  with st.sidebar:
    status_map = {
        "online": ("نشط 🟢", "online-dot"),
        "busy": ("مشغول 🟠", "busy-dot"),
        "offline": ("غير متصل 🔴", "offline-dot"),
    }
    curr_s, _ = status_map.get(
        st.session_state.get("status", "online"), ("نشط 🟢", "online-dot")
    )
    st.write(
        f"### {st.session_state.get('avatar', '😀')} {st.session_state.get('username', '')}"
    )
    st.caption(f"{st.session_state.get('bio', '')} | {curr_s}")

    with st.expander("⚙️ إعدادات الحساب والخصوصية"):
      new_bio = st.text_input(
          "النبذة (Bio)", value=st.session_state.get("bio", "")
      )
      avatars = ["😀", "😎", "🦊", "🤖", "🐱", "🚀"]
      cur_av = st.session_state.get("avatar", "😀")
      idx = avatars.index(cur_av) if cur_av in avatars else 0
      new_avatar = st.selectbox("تغيير الرمز", avatars, index=idx)

      status_options = ["online", "busy", "offline"]
      cur_st = st.session_state.get("status", "online")
      st_idx = status_options.index(cur_st) if cur_st in status_options else 0
      new_status = st.selectbox(
          "تحديد الحالة",
          status_options,
          index=st_idx,
          format_func=lambda x: {
              "online": "نشط (Online)",
              "busy": "مشغول (Busy)",
              "offline": "غير متصل (Offline)",
          }[x],
      )
      if st.button("حفظ الملف الشخصي"):
        c.execute(
            "UPDATE users SET bio=?, avatar=?, status=? WHERE username=?",
            (
                new_bio,
                new_avatar,
                new_status,
                st.session_state["username"],
            ),
        )
        conn.commit()
        st.session_state["bio"] = new_bio
        st.session_state["avatar"] = new_avatar
        st.session_state["status"] = new_status
        st.success("تم تحديث الملف الشخصي!")
        st.rerun()

      st.markdown("---")
      st.write("🔑 **تغيير كلمة المرور**")
      old_p = st.text_input("كلمة المرور الحالية", type="password")
      new_p = st.text_input("كلمة المرور الجديدة", type="password")
      if st.button("تحديث كلمة المرور"):
        c.execute(
            "SELECT password_hash FROM users WHERE username=?",
            (st.session_state["username"],),
        )
        row = c.fetchone()
        if row and hash_password(old_p) == row:
          c.execute(
              "UPDATE users SET password_hash=? WHERE username=?",
              (hash_password(new_p), st.session_state["username"]),
          )
          conn.commit()
          st.success("تم تغيير كلمة المرور بنجاح!")
        else:
          st.error("كلمة المرور الحالية غير صحيحة!")

    if st.button("تسجيل الخروج"):
      st.session_state["logged_in"] = False
      st.session_state["active_chat"] = None
      st.rerun()

    st.markdown("---")
    st.subheader("🔍 بحث عن أصدقاء")
    search_query = st.text_input("ابحث باسم المستخدم...", "")

    st.subheader("👥 المحادثات")
    c.execute(
        "SELECT username, avatar, status FROM users WHERE username != ?",
        (st.session_state["username"],),
    )
    all_users = c.fetchall()

    filtered_users = [
        u
        for u in all_users
        if search_query.lower() in u[0].lower() or not search_query
    ]

    for friend_name, friend_avatar, friend_status in filtered_users:
      c.execute(
          "SELECT COUNT(*) FROM messages WHERE sender=? AND receiver=? AND"
          " is_read=0",
          (friend_name, st.session_state["username"]),
      )
      unread_row = c.fetchone()
      unread_count = unread_row if unread_row else 0

      dot_symbol = (
          "🟢"
          if friend_status == "online"
          else ("🟠" if friend_status == "busy" else "🔴")
      )
      unread_str = (
          f" [غير مقروء: {unread_count}]" if unread_count > 0 else ""
      )

      if st.button(
          f"{friend_avatar} {friend_name} {dot_symbol}{unread_str}",
          key=f"chat_{friend_name}",
      ):
        st.session_state["active_chat"] = friend_name
        c.execute(
            "UPDATE messages SET is_read=1 WHERE sender=? AND receiver=?",
            (friend_name, st.session_state["username"]),
        )
        conn.commit()
        st.rerun()

  if st.session_state.get("active_chat"):
    target_friend = st.session_state["active_chat"]
    c.execute(
        "SELECT avatar, status, bio FROM users WHERE username=?",
        (target_friend,),
    )
    f_info = c.fetchone()
    f_av, f_status, f_bio = (
        f_info if f_info else ("💬", "online", "لا توجد نبذة")
    )
    dot_sym = (
        "🟢 نشط الآن"
        if f_status == "online"
        else ("🟠 مشغول" if f_status == "busy" else "🔴 غير متصل")
    )

    col_t1, col_t2 = st.columns()
    with col_t1:
      st.title(f"{f_av} {target_friend}")
      st.caption(f"{f_bio} | الحالة: {dot_sym}")
    with col_t2:
      with st.expander("⚙️ إعدادات المحادثة"):
        if st.button("🗑️ مسح المحادثة معي"):
          c.execute(
              """DELETE FROM messages WHERE 
                         (sender=? AND receiver=?) OR (sender=? AND receiver=?)""",
              (
                  st.session_state["username"],
                  target_friend,
                  target_friend,
                  st.session_state["username"],
              ),
          )
          conn.commit()
          st.success("تم مسح المحادثة!")
          st.rerun()

    st.markdown("---")

    c.execute(
        """
        SELECT id, sender, avatar, text, ts, is_read FROM messages 
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

    for msg_id, sender_u, av, txt, time, is_read in c.fetchall():
      is_me = sender_u == st.session_state["username"]
      with st.chat_message("user" if is_me else "assistant"):
        st.markdown(f"{av} **{sender_u}**: {txt}")
        read_status = (
            " ✓✓ مقروءة"
            if (is_me and is_read == 1)
            else (" ✓ أُرسلت" if is_me else "")
        )
        st.caption(f"{time}{read_status}")

    if prompt := st.chat_input(f"اكتب رسالة إلى {target_friend}..."):
      current_time = datetime.datetime.now().strftime("%H:%M")
      c.execute(
          "INSERT INTO messages (sender, receiver, avatar, text, ts,"
          " is_read) VALUES (?, ?, ?, ?, ?, 0)",
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
