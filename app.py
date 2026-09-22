import datetime
import sqlite3
import streamlit as st

conn = sqlite3.connect("chat.db", check_same_thread=False)
c = conn.cursor()
c.execute(
    """CREATE TABLE IF NOT EXISTS messages 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, text TEXT, ts TEXT)"""
)
conn.commit()

st.set_page_config(page_title="Messenger Pro", page_icon="💬")
st.title("💬 ماسنجر الأصدقاء")

with st.sidebar:
  st.header("⚙️ إعدادات الهوية")
  my_name = st.text_input("اسمك الظاهر:", value="محمد")
  st.markdown("---")
  if st.button("🗑️ مسح سجل المحادثة"):
    c.execute("DELETE FROM messages")
    conn.commit()
    st.rerun()

c.execute("SELECT id, user, text, ts FROM messages ORDER BY id ASC")
for msg_id, u, txt, time in c.fetchall():
  is_me = u == my_name
  with st.chat_message("user" if is_me else "assistant"):
    st.markdown(f"**{u}**: {txt}")
    st.caption(time)

if prompt := st.chat_input("اكتب رسالتك واضغط Enter..."):
  current_time = datetime.datetime.now().strftime("%H:%M")
  c.execute(
      "INSERT INTO messages (user, text, ts) VALUES (?, ?, ?)",
      (my_name, prompt, current_time),
  )
  conn.commit()
  st.rerun()