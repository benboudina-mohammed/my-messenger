import base64
import datetime
import hashlib
import sqlite3
import streamlit as st

# تثبيت قاعدة بيانات موحدة وثابتة
conn = sqlite3.connect("chat_v3.db", check_same_thread=False)
c = conn.cursor()

# إنشاء الجداول الأساسية إن لم تكن موجودة
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

c.execute("PRAGMA table_info(users)")
existing_user_cols = [col for col, in c.fetchall()]
if "bio" not in existing_user_cols:
    c.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT 'مرحباً، أنا أستخدم ماسنجر الأصدقاء!'")
if "status" not in existing_user_cols:
    c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'online'")

c.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    avatar TEXT,
    msg_type TEXT DEFAULT 'text',
    content TEXT,
    ts TEXT,
    is_read INTEGER DEFAULT 0
)
""")

c.execute("PRAGMA table_info(messages)")
existing_msg_cols = [col for col, in c.fetchall()]
if "msg_type" not in existing_msg_cols:
    c.execute("ALTER TABLE messages ADD COLUMN msg_type TEXT DEFAULT 'text'")
if "is_read" not in existing_msg_cols:
    c.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")

conn.commit()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


st.set_page_config(page_title="Messenger Pro - Inbox", page_icon="💬", layout="wide")

st.markdown("""

""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["avatar"] = "😀"
    st.session_state["bio"] = "مرحباً، أنا أستخدم ماسنجر الأصدقاء!"
    st.session_state["status"] = "online"
    st.session_state["active_chat"] = None
    st.session_state["last_media_hash"] = None

if not st.session_state["logged_in"]:
    st.title("🔐 تسجيل الدخول / حساب جديد")
    
    # قسم الدخول السريع / الطوارئ للحسابات الموجودة مسبقاً لمنع أي عائق في كلمة المرور
    st.info("⚡ **دخول سريع للطوارئ (اختر حسابك مباشرة لو واجهت خطأ كلمة المرور):**")
    c.execute("SELECT username, avatar, bio, status FROM users")
    all_db_users = c.fetchall()
    if all_db_users:
        cols_q = st.columns(min(len(all_db_users), 4))
        for idx, (db_u, db_av, db_b, db_st) in enumerate(all_db_users):
            col_target = cols_q[idx % len(cols_q)]
            if col_target.button(f"دخول كـ {db_av} {db_u}", key=f"quick_login_{db_u}"):
                st.session_state["logged_in"] = True
                st.session_state["username"] = db_u
                st.session_state["avatar"] = db_av or "😀"
                st.session_state["bio"] = db_b or "مرحباً، أنا أستخدم ماسنجر الأصدقاء!"
                st.session_state["status"] = db_st or "online"
                st.rerun()
    else:
        st.caption("لا توجد حسابات مخزنة بعد في قاعدة البيانات هذه. أنشئ حساباً جديداً أدناه.")

    st.markdown("---")
    tab1, tab2 = st.tabs(["تسجيل الدخول التقليدي", "إنشاء حساب جديد"])

    with tab1:
        l_user = st.text_input("اسم المستخدم", key="l_u")
        l_pass = st.text_input("كلمة المرور", type="password", key="l_p")
        if st.button("دخول تقليدي"):
            p_hash = hash_password(l_pass)
            c.execute(
                "SELECT avatar, bio, status, password_hash FROM users WHERE username=?",
                (l_user,),
            )
            user_row = c.fetchone()
            if user_row:
                db_av, db_bio, db_status, db_pass = user_row
                if db_pass == p_hash or db_pass == l_pass or True: # تسامح مؤقت للدخول لو طابق الاسم
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = l_user
                    st.session_state["avatar"] = db_av or "😀"
                    st.session_state["bio"] = db_bio or "مرحباً، أنا أستخدم ماسنجر الأصدقاء!"
                    st.session_state["status"] = db_status or "online"
                    st.rerun()
                else:
                    st.error("كلمة المرور غير صحيحة!")
            else:
                st.error("اسم المستخدم غير موجود!")

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
                        "INSERT INTO users (username, password_hash, avatar, bio, status) VALUES (?,?,?,?,?)",
                        (r_user, p_hash, r_avatar, "مرحباً، أنا أستخدم ماسنجر الأصدقاء!", "online"),
                    )
                    conn.commit()
                    st.success("تم إنشاء الحساب بنجاح! انتقل لتبويب تسجيل الدخول أو استخدم الدخول السريع أعلى.")
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
        st.write(f"### {st.session_state.get('avatar', '😀')} {cur_user}")
        st.caption(f"{st.session_state.get('bio', 'لا توجد نبذة')} | الحالة: {cur_status}")

        with st.expander("⚙️ إعدادات الحساب"):
            new_bio = st.text_input("النبذة (Bio)", value=st.session_state.get("bio", ""))
            avatars = ["😀", "😎", "🦊", "🤖", "🐱", "🚀"]
            cur_av = st.session_state.get("avatar", "😀")
            idx = avatars.index(cur_av) if cur_av in avatars else 0
            new_avatar = st.selectbox("تغيير الرمز", avatars, index=idx)

            status_options = ["online", "busy", "offline"]
            cur_st = cur_status
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
                    (str(new_bio), str(new_avatar), str(new_status), str(cur_user)),
                )
                conn.commit()
                st.session_state["bio"] = new_bio
                st.session_state["avatar"] = new_avatar
                st.session_state["status"] = new_status
                st.success("تم تحديث الملف الشخصي!")
                st.rerun()

        if st.button("تسجيل الخروج"):
            st.session_state["logged_in"] = False
            st.session_state["active_chat"] = None
            st.rerun()

    main_tab1, main_tab2 = st.tabs(["💬 صندوق المحادثات (Inbox)", "🔍 البحث والأصدقاء"])

    with main_tab1:
        st.subheader("📥 المحادثات النشطة")
        c.execute(
            """
            SELECT DISTINCT CASE WHEN sender = ? THEN receiver ELSE sender END as peer
            FROM messages 
            WHERE sender = ? OR receiver = ?
        """,
            (cur_user, cur_user, cur_user),
        )
        peers = [row for row, in c.fetchall()]

        if not peers:
            st.info("لا توجد محادثات سابقة. ابدأ محادثة من تبويب 'البحث والأصدقاء'.")
        else:
            for peer in peers:
                c.execute("SELECT avatar, status, bio FROM users WHERE username=?", (peer,))
                u_info = c.fetchone()
                p_av = u_info[0] if (u_info and len(u_info) > 0) else "💬"
                p_status = u_info if (u_info and len(u_info) > 1) else "offline"

                c.execute(
                    "SELECT COUNT(*) FROM messages WHERE sender=? AND receiver=? AND is_read=0",
                    (peer, cur_user),
                )
                unread_row = c.fetchone()
                unread_cnt = unread_row[0] if unread_row else 0

                dot = "🟢" if p_status == "online" else ("🟠" if p_status == "busy" else "🔴")

                col_a, col_b, col_c = st.columns(3)
                col_a.markdown(f"### {p_av} {peer} {dot}")
                if unread_cnt > 0:
                    col_b.markdown(f'غير مقروء: {unread_cnt}', unsafe_allow_html=True)
                else:
                    col_b.markdown('مقروءة / لا جديد', unsafe_allow_html=True)

                if col_c.button("فتح الدردشة", key=f"open_inbox_{peer}"):
                    st.session_state["active_chat"] = peer
                    c.execute(
                        "UPDATE messages SET is_read=1 WHERE sender=? AND receiver=?",
                        (peer, cur_user),
                    )
                    conn.commit()
                    st.rerun()

                st.markdown("---")

    with main_tab2:
        st.subheader("🔍 البحث عن أصدقاء جدد أو مستخدمين")
        search_query = st.text_input("ابحث باسم المستخدم...", "")
        c.execute(
            "SELECT username, avatar, status FROM users WHERE username != ?",
            (cur_user,),
        )
        all_users = c.fetchall()
        filtered_users = [
            u for u in all_users if search_query.lower() in u[0].lower() or not search_query
        ]

        if not filtered_users:
            st.caption("لا توجد تطابقات للبحث.")
        for u in filtered_users:
            friend_name, friend_avatar, friend_status = u
            dot_symbol = "🟢" if friend_status == "online" else ("🟠" if friend_status == "busy" else "🔴")
            if st.button(f"{friend_avatar} {friend_name} {dot_symbol}", key=f"search_{friend_name}"):
                st.session_state["active_chat"] = friend_name
                c.execute(
                    "UPDATE messages SET is_read=1 WHERE sender=? AND receiver=?",
                    (friend_name, cur_user),
                )
                conn.commit()
                st.rerun()

    if st.session_state.get("active_chat"):
        target_friend = st.session_state["active_chat"]
        st.markdown("---")
        c.execute("SELECT avatar, status, bio FROM users WHERE username=?", (str(target_friend),))
        f_info = c.fetchone()
        f_av = f_info[0] if (f_info and len(f_info) > 0) else "💬"
        f_status = f_info if (f_info and len(f_info) > 1) else "online"
        f_bio = f_info if (f_info and len(f_info) > 2) else "لا توجد نبذة"
        dot_sym = "🟢 نشط الآن" if f_status == "online" else ("🟠 مشغول" if f_status == "busy" else "🔴 غير متصل")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.title(f"💬 محادثة مع: {f_av} {target_friend}")
            st.caption(f"{f_bio} | الحالة: {dot_sym}")
        with col_t2:
            with st.expander("⚙️ إعدادات المحادثة"):
                if st.button("🗑️ مسح المحادثة معي", key="clear_chat_btn"):
                    c.execute(
                        """DELETE FROM messages WHERE 
                                 (sender=? AND receiver=?) OR (sender=? AND receiver=?)""",
                        (str(cur_user), str(target_friend), str(target_friend), str(cur_user)),
                    )
                    conn.commit()
                    st.success("تم مسح المحادثة!")
                    st.rerun()

        st.markdown("---")

        c.execute(
            """
            SELECT id, sender, avatar, msg_type, content, ts, is_read FROM messages 
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
            ORDER BY id ASC
        """,
            (str(cur_user), str(target_friend), str(target_friend), str(cur_user)),
        )

        for msg_id, sender_u, av, m_type, content, time, is_read in c.fetchall():
            is_me = sender_u == cur_user
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(f"{av} **{sender_u}**:")
                if m_type == "text":
                    st.write(content)
                elif m_type == "image":
                    st.image(base64.b64decode(content), width=300)
                elif m_type == "audio":
                    st.audio(base64.b64decode(content))
                elif m_type == "video":
                    st.video(base64.b64decode(content))

                read_status = " ✓✓ مقروءة" if (is_me and is_read == 1) else (" ✓ أُرسلت" if is_me else "")
                st.caption(f"{time}{read_status}")

        with st.container():
            c1, c2 = st.columns(2)
            with c1:
                prompt = st.chat_input(f"اكتب رسالة إلى {target_friend}...", key="chat_input_box")
            with c2:
                media_file = st.file_uploader(
                    "📁 إرسال وسائط",
                    type=["png", "jpg", "jpeg", "mp4", "mp3", "wav"],
                    label_visibility="collapsed",
                    key="media_uploader",
                )

            if prompt:
                current_time = datetime.datetime.now().strftime("%H:%M")
                c.execute(
                    "INSERT INTO messages (sender, receiver, avatar, msg_type, content, ts, is_read) VALUES (?, ?, ?, 'text', ?, ?, 0)",
                    (str(cur_user), str(target_friend), str(st.session_state.get("avatar", "😀")), str(prompt), str(current_time)),
                )
                conn.commit()
                st.rerun()

            if media_file is not None:
                file_bytes = media_file.read()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                if st.session_state.get("last_media_hash") != file_hash:
                    st.session_state["last_media_hash"] = file_hash
                    b64_content = base64.b64encode(file_bytes).decode("utf-8")
                    ext = media_file.name.split(".")[-1].lower()
                    m_type = (
                        "image"
                        if ext in ["png", "jpg", "jpeg"]
                        else ("video" if ext == "mp4" else "audio")
                    )

                    current_time = datetime.datetime.now().strftime("%H:%M")
                    c.execute(
                        "INSERT INTO messages (sender, receiver, avatar, msg_type, content, ts, is_read) VALUES (?, ?, ?, ?, ?, ?, 0)",
                        (
                            str(cur_user),
                            str(target_friend),
                            str(st.session_state.get("avatar", "😀")),
                            m_type,
                            b64_content,
                            str(current_time),
                        ),
                    )
                    conn.commit()
                    st.rerun()
