import streamlit as st
st.title("resume app")
name=st.text_input("名前")
country=("出身国",["nepal","sri-lanka","vietnam","japan"])
pr=st.text_area("自己 PR")
char_count=len(pr)
if pr:
    st.write(f"現在の文字数:{char_count}")
clicked=st.button("表示")
if clicked:
  if char_count<100:
    st.error("文字巣が足りません")

if clicked:
    st.success("ok")
    st.write("===入力内容===")
    st.write(f"名前:{name}")
    st.write(f"出身国:{country}")
    st.write(f"自己 PR:{pr}")
    
       