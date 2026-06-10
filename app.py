import streamlit as st 
st.title("my profile")
name = st.text_input("name")
country = st.text_input("country")
hobby = st.text_input("hobby")
if name:
    st.write(f"my name is{name}")
if country:
    st.write(f"i am from{country}")
if hobby:
    st.write(f"my hobby is{hobby}")
