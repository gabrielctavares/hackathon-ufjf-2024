import streamlit as st
from views.config_page import configure_series, initialize_series_configurations
from views.register_page import show_register
from views.visualization_page import show_visualization

initialize_series_configurations()

# Continuar com o restante do app
if st.session_state["config"]:
    st.sidebar.write(f"Série Ativa: {st.session_state['config']['nome_serie']}")
else:
    menu = "Configurar Série"

st.title("Sistema de Detecção de Anomalias com IA")
menu = st.sidebar.radio("Menu", ["Configurar Série", "Visualizar Dados", "Cadastrar Dados"])


if menu == "Configurar Série":
   configure_series()
elif menu == "Visualizar Dados":
    show_visualization()
elif menu == "Cadastrar Dados":
    show_register() 
