import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Classificador de Flores Iris")

# Login
if "token" not in st.session_state:
    st.session_state.token = None

if st.session_state.token is None:
    with st.form("login"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            r = requests.post(
                f"{API_URL}/login",
                json={"username": username, "password": password},
                timeout=30,
            )
            if r.status_code == 200:
                st.session_state.token = r.json()["access_token"]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
else:
    st.success("Autenticado")
    col1, col2 = st.columns(2)
    sepal_length = col1.number_input("Sepal length (cm)", 0.0, 10.0, 5.1)
    sepal_width = col1.number_input("Sepal width (cm)", 0.0, 10.0, 3.5)
    petal_length = col2.number_input("Petal length (cm)", 0.0, 10.0, 1.4)
    petal_width = col2.number_input("Petal width (cm)", 0.0, 10.0, 0.2)

    if st.button("Classificar"):
        r = requests.post(
            f"{API_URL}/predict",
            json={
                "sepal_length": sepal_length,
                "sepal_width": sepal_width,
                "petal_length": petal_length,
                "petal_width": petal_width,
            },
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=30,
        )
        if r.status_code == 200:
            dados = r.json()
            st.subheader(f"Espécie: {dados['classe']}")
            st.bar_chart(dados["probabilidades"])
        elif r.status_code == 401:
            st.session_state.token = None
            st.warning("Sessão expirada. Faça login de novo.")
            st.rerun()
        else:
            st.error(f"Erro {r.status_code}: {r.text}")

    if st.button("Sair"):
        st.session_state.token = None
        st.rerun()
