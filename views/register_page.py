import pandas as pd
import streamlit as st
from database.dynamic_table_service import save_data, load_columns_info

def show_register():
    # Recuperar a configuração ativa da série
    config = st.session_state.get("config", {})
    if not config:
        st.warning("Nenhuma configuração de série ativa encontrada.")
        return

    st.write(f"### Cadastro Manual para a Série: {config['nome_serie']}")

    table_name = config["dynamic_table_name"]
    columns_info = load_columns_info(table_name)
    
    dynamic_inputs = {}
    with st.form("Cadastro Manual"):
        for idx, col_info in enumerate(columns_info):
            col_name = col_info["name"]
            col_type = col_info["type"]

            # Ignorar colunas automáticas ou específicas como ID
            if col_name in ["id", "anomalia", "correcao_sugerida"]:
                continue

            # Gerar campo com base no tipo de dado
            if "FLOAT" in str(col_type).upper() or "DECIMAL" in str(col_type).upper():
                dynamic_inputs[col_name] = st.number_input(
                    f"{col_name.capitalize()}",
                    min_value=0.0,
                    key=f"float_{idx}"
                )
            elif "INTEGER" in str(col_type).upper():
                dynamic_inputs[col_name] = st.number_input(
                    f"{col_name.capitalize()}",
                    min_value=0,
                    step=1,
                    key=f"integer_{idx}"
                )
            elif "BOOLEAN" in str(col_type).upper():
                dynamic_inputs[col_name] = st.checkbox(
                    f"{col_name.capitalize()} (Verdadeiro/Falso)",
                    key=f"boolean_{idx}"
                )
            elif "VARCHAR" in str(col_type).upper() or "TEXT" in str(col_type).upper():
                dynamic_inputs[col_name] = st.text_input(
                    f"{col_name.capitalize()}",
                    key=f"text_{idx}"
                )

        submit = st.form_submit_button("Salvar")
        if submit:
            # Validar se todos os campos foram preenchidos
            if all(dynamic_inputs.values() or isinstance(dynamic_inputs[key], bool) for key in dynamic_inputs):
                novo_dado = pd.DataFrame([dynamic_inputs])
                save_data(table_name, novo_dado, config)
                st.success("Dado salvo com sucesso!")
            else:
                st.error("Preencha todos os campos corretamente antes de salvar.")


    # Upload de planilha    
    st.write(f"### Importar Dados de Planilha para a Série: {config['nome_serie']}")
    uploaded_file = st.file_uploader("Escolha um arquivo Excel ou CSV", type=["xlsx", "csv"])
    if uploaded_file:
        try:
            # Processar arquivo importado
            if uploaded_file.name.endswith(".xlsx"):
                imported_data = pd.read_excel(uploaded_file)
            else:
                imported_data = pd.read_csv(uploaded_file)

            # Exibir os dados importados
            st.write("### Dados Importados")
            st.dataframe(imported_data)

            # Verificar estrutura do arquivo
            required_columns = set(config["auxiliary_variables"] + [config["series_column"], config["analysis_variable"]])
            if not required_columns.issubset(imported_data.columns):
                st.error(f"A planilha deve conter as colunas: {', '.join(required_columns)}")
            else:
                # Salvar dados no banco de dados
                if st.button("Salvar Dados Importados"):
                    save_data(config["dynamic_table_name"], imported_data, config)
                    st.success("Dados importados e salvos com sucesso!")

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
