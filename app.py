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
    avatar TEXT,
    bio TEXT,
    status TEXT
)
""")

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

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["username"] = ""
  st.session_state["avatar"] = "😀"
  st.session_state["bio"] = "مرحباً، أنا أستخدم ماسنجر الأصدقاء!"
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
        st.session_state["avatar"] = res[0] or "😀"
        st.session_state["bio"] = res or "مرحباً!"
        st.session_state["status"] = res or "online"
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
  cur_user = st.session_state.get("username", "")
  cur_status = st.session_state.get("status", "online")

  if cur_user:
    c.execute(
        "UPDATE users SET status=? WHERE username=?",
        (str(cur_status), str(cur_user)),
    )
    conn.commit()

  with st.sidebar:
    st.write(
        f"### {st.session_state.get('avatar', '😀')} {cur_user}"
    )
    st.caption(f"{st.session_state.get('bio', '')} | الحالة: {cur_status}")

    with st.expander("⚙️ إعدادات الحساب والخصوصية"):
      new_bio = st.text_input(
          "النبذة (Bio)", value=st.session_state.get("bio", "")
      )
      avatars = ["😀", "😎", "🦊", "🤖", "🐱", "🚀"]
      cur_av = st.session_state.get("avatar", "😀")
      idx = avatars.index(cur_av) if cur_av in avatars else 0
      new_avatar = st.selectbox("تغيير الرمز", avatars, index=idx)

      status_options = ["online", "busy", "offline"]
      st_idx = (
          status_options.index(cur_status)
          if cur_status in status_options
          else 0
      )
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
            (str(new_bio), str(new_avatar), str(new_status), str(cur_user)),
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
            "SELECT password_hash FROM users WHERE username=?", (str(cur_user),)
        )
        row = c.fetchone()
        if row and hash_password(old_p) == row[0]:
          c.execute(
              "UPDATE users SET password_hash=? WHERE username=?",
              (hash_password(new_p), str(cur_user)),
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
        (str(cur_user),),
    )
    all_users = c.fetchall()

    filtered_users = [
        u
        for u in all_users
        if search_query.lower() in u.lower() or not search_query
    ]

    for friend_name, friend_avatar, friend_status in filtered_users:
      c.execute(
          "SELECT COUNT(*) FROM messages WHERE sender=? AND receiver=? AND"
          " is_read=0",
          (str(friend_name), str(cur_user)),
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
            (str(friend_name), str(cur_user)),
        )
        conn.commit()
        st.rerun()

  if st.session_state.get("active_chat"):
    target_friend = st.session_state["active_chat"]
    c.execute(
        "SELECT avatar, status, bio FROM users WHERE username=?",
        (str(target_friend),),
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
                  str(cur_user),
                  str(target_friend),
                  str(target_friend),
                  str(cur_user),
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
            str(cur_user),
            str(target_friend),
            str(target_friend),
            str(cur_user),
        ),
    )

    for msg_id, sender_u, av, txt, time, is_read in c.fetchall():
      is_me = sender_u == cur_user
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
              str(cur_user),
              str(target_friend),
              str(st.session_state.get("avatar", "😀")),
              str(prompt),
              str(current_time),
          ),
      )
      conn.commit()
      st.rerun()
  else:
    st.title("💬 ماسنجر الأصدقاء")
    st.info("👈 اختر صديقاً من القائمة الجانبية أو ابحث عنه لبدء محادثة خاصة.")
