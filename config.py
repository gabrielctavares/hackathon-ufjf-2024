import streamlit as st
import pandas as pd

def show_config():
    st.title("Configuração da Série Histórica")

    # Carregar a planilha
    uploaded_file = st.file_uploader("Carregue sua planilha (CSV ou Excel):", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Ler a planilha
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("Pré-visualização da Planilha:")
        st.dataframe(df)

        # Seletor de funções para cada coluna
        st.write("### Escolha a Função de Cada Coluna")
        column_roles = {}

        for column in df.columns:
            column_roles[column] = st.selectbox(
                f"Selecione a função da coluna `{column}`:",
                [
                    "Nenhum",
                    "Valor Avaliado (Target)",
                    "Feature (Contribui para o Modelo)",
                    "Regra (Define Regras)",
                ],
            )

        st.write("### Configuração Selecionada:")
        target_column = None
        feature_columns = []
        rule_columns = []

        for column, role in column_roles.items():
            if role == "Valor Avaliado (Target)":
                if target_column is not None:
                    st.warning(f"Mais de uma coluna selecionada como Valor Avaliado! Apenas `{target_column}` será usada.")
                target_column = column
            elif role == "Feature (Contribui para o Modelo)":
                feature_columns.append(column)
            elif role == "Regra (Define Regras)":
                rule_columns.append(column)

        st.write("**Valor Avaliado:**", target_column)
        st.write("**Features Selecionadas:**", feature_columns)
        st.write("**Colunas de Regras:**", rule_columns)

        # Confirmar configuração
        if st.button("Confirmar Configuração"):
            if not target_column:
                st.error("Você precisa selecionar uma coluna como Valor Avaliado!")
            elif not feature_columns:
                st.error("Você precisa selecionar pelo menos uma coluna como Feature!")
            else:
                st.success("Configuração confirmada com sucesso!")
                st.write("**Configuração Final:**")
                st.write("- Valor Avaliado:", target_column)
                st.write("- Features:", feature_columns)
                st.write("- Regras:", rule_columns)

                # Gerar um DataFrame processado para o modelo
                processed_df = df[feature_columns + [target_column] + rule_columns]
                st.write("Pré-processamento dos Dados:")
                st.dataframe(processed_df)

                # Salvar o DataFrame configurado
                csv_data = processed_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Baixar Dados Configurados",
                    data=csv_data,
                    file_name="dados_configurados.csv",
                    mime="text/csv",
                )

