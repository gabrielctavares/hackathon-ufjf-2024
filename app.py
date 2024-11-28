import streamlit as st
from config import show_config
from database_service import load_data
from register import show_register
import train_model
from visualization import show_visualization


st.title("Sistema de Detecção de Anomalias na Produção de Leite com IA")
menu = st.sidebar.radio("Menu", ["Visualizar Dados", "Cadastrar Dados", "Configurações", "Detectar Anomalias"])

# Visualizar Dados
if menu == "Visualizar Dados":
    show_visualization()
# Cadastrar Dados
elif menu == "Cadastrar Dados":
    show_register() 
# Treinar Modelo
elif menu == "Configurações":
   show_config()

# Detectar Anomalias
elif menu == "Detectar Anomalias":
    st.write("### Detecção de Anomalias com IA")
    data = load_data()
    if data.empty:
        st.warning("Não há dados para validar.")
    else:        
        data["media_anterior"] = data.groupby("raca")["producao_kg"].transform(lambda x: x.expanding().mean().shift(1))
        data["ultimo_valor"] = data.groupby("raca")["producao_kg"].shift(1)
        data = train_model.infer_with_model(data)
