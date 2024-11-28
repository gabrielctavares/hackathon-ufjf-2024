import pandas as pd
import streamlit as st

from database_service import save_data

def show_register():
    st.write("### Cadastro Manual")

    # Formulário para entrada manual
    with st.form("Cadastro Manual"):
        semana = st.number_input("Semana", min_value=1, step=1)
        raca = st.selectbox("Raça", ["Holandesa", "Jersey", "Gir"])
        producao = st.number_input("Produção (kg)", min_value=0.0)
        submit = st.form_submit_button("Salvar")
        if submit:
            if semana and raca and producao >= 0:
                novo_dado = pd.DataFrame([{"semana": semana, "raca": raca, "producao_kg": producao}])
                save_data(novo_dado)
            else:
                st.error("Preencha todos os campos corretamente antes de salvar.")

    # Upload de planilha    
    st.write("### Importar Dados de Planilha")
    uploaded_file = st.file_uploader("Escolha um arquivo Excel ou CSV", type=["xlsx", "csv"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".xlsx"):
                imported_data = pd.read_excel(uploaded_file)
            else:
                imported_data = pd.read_csv(uploaded_file)

            # Exibir os dados importados
            st.write("### Dados Importados")
            st.dataframe(imported_data)

            # Verificar estrutura do arquivo
            required_columns = {"semana", "raca", "producao_kg"}
            if not required_columns.issubset(imported_data.columns):
                st.error(f"A planilha deve conter as colunas: {', '.join(required_columns)}")
            else:
                # Salvar no banco de dados
                if st.button("Salvar Dados Importados"):
                    save_data(imported_data)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")


