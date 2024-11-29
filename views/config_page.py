import streamlit as st
import pandas as pd
from database.configuration_service import save_configuration, get_all_configurations
from database.dynamic_table_service import create_dynamic_table, save_data


def initialize_series_configurations():
    if "config" not in st.session_state:
        st.session_state["config"] = None  

    configuracoes = get_all_configurations()

    if configuracoes:
        if st.session_state["config"] is None:
            st.session_state["config"] = configuracoes[0]  
    else:
        st.warning("Nenhuma configuração encontrada. Por favor, crie uma configuração.")


def register_serie(): 
    uploaded_file = st.file_uploader("Carregar Dados (Excel/CSV)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_excel(uploaded_file)

            st.success("Planilha carregada com sucesso!")
            st.write("Dados Detectados:")
            st.dataframe(data)

            st.session_state["uploaded_data"] = data
            st.write("### Configurações de Série")

            default_nome_serie = uploaded_file.name.rsplit(".", 1)[0]
            nome_serie = st.text_input("Nome da Configuração", value=default_nome_serie)
            dynamic_table_name = f"serie_{nome_serie.lower().replace(' ', '_')}"

            series_column = st.selectbox("Coluna que identifica a série", options=data.columns)

            possible_analysis_vars = [col for col in data.columns if pd.api.types.is_numeric_dtype(data[col]) and col != series_column]
            default_analysis_variable = possible_analysis_vars[0] if possible_analysis_vars else data.columns[0]
            analysis_variable = st.selectbox(
                "Variável de análise", options=possible_analysis_vars, index=possible_analysis_vars.index(default_analysis_variable)
            )

            auxiliary_variables = st.multiselect(
                "Variáveis auxiliares (features)",
                options=[col for col in data.columns if col != analysis_variable],
                default=[col for col in data.columns if col != analysis_variable and col != series_column],
            )

            st.write("### Filtros Aplicáveis") 
            filters = {}
            for col in data.columns:
                if col == analysis_variable:
                    continue
                if pd.api.types.is_numeric_dtype(data[col]):
                    if pd.api.types.is_integer_dtype(data[col]):
                        min_value, max_value = int(data[col].min()), int(data[col].max())
                    else:
                        min_value, max_value = float(data[col].min()), float(data[col].max())                    
                    
                    filters[col] = st.slider(
                        f"Filtrar por {col} (intervalo)", min_value=min_value, max_value=max_value, value=(min_value, max_value)
                    )
                else:
                    unique_values = data[col].unique()
                    if len(unique_values) <= 10:
                        filters[col] = st.multiselect(f"Filtrar por {col}", options=unique_values, default=unique_values)

             # Adicionar configuração de contaminação
            st.write("### Configurações de Validação da IA")
            contamination = st.number_input(
                "Nível de Contaminação dos Dados (entre 0.005 e 0.5)",
                min_value=0.005,
                max_value=0.5,
                value=0.05,
                step=0.005,
                format="%.3f"
            )

            st.write("### Configurações de Validação")
            validation_options = {}

            if st.checkbox("Definir valores mínimos e máximos?"):
                min_value = st.number_input(f"Valor mínimo para {analysis_variable}", value=0.0, step=0.1)
                max_value = st.number_input(f"Valor máximo para {analysis_variable}", value=100.0, step=0.1)
                validation_options["min_value"] = min_value
                validation_options["max_value"] = max_value

            if st.checkbox("Validar relação com médias e últimos valores?"):
                validate_mean = st.checkbox("Validar relação com a média dos valores anteriores?")
                mean_threshold = st.number_input("Limite (em %) acima da média", value=20, step=1, disabled=not validate_mean)

                validate_last = st.checkbox("Validar relação com o último valor lançado?")
                last_threshold = st.number_input("Limite (em %) acima do último valor", value=40, step=1, disabled=not validate_last)

                validation_options["validate_mean"] = validate_mean
                validation_options["mean_threshold"] = mean_threshold
                validation_options["validate_last"] = validate_last
                validation_options["last_threshold"] = last_threshold

            
            if st.button("Salvar Configurações"):
                config = {
                    "nome_serie": nome_serie,
                    "series_column": series_column,
                    "analysis_variable": analysis_variable,
                    "auxiliary_variables": auxiliary_variables,
                    "filters": filters,
                    "validations": validation_options,
                    "contamination": contamination, 
                    "dynamic_table_name": dynamic_table_name,
                }
                st.session_state["config"] = config
                save_configuration(config)
                
                create_dynamic_table(dynamic_table_name, data)                
                save_data(dynamic_table_name, data, config)
                st.success("Configurações salvas com sucesso!")

        except Exception as e:
            st.error(f"Erro ao carregar a planilha: {e}")


def select_config():
    configuracoes = get_all_configurations()

    if not configuracoes:
        st.warning("Nenhuma configuração de série encontrada.")
        return

    st.write("#### Configurações Disponíveis")
    config_names = [config["nome_serie"] for config in configuracoes]
    selected_config = st.selectbox("Selecione uma configuração:", options=config_names)

    if selected_config:
        selected_config_details = next(config for config in configuracoes if config["nome_serie"] == selected_config)
        
        st.markdown("#### Informações Principais")
        st.write(f"**Nome da Série:** {selected_config_details['nome_serie']}")
        st.write(f"**Coluna de Identificação da Série:** {selected_config_details['series_column']}")
        st.write(f"**Variável de Análise:** {selected_config_details['analysis_variable']}")
        
        st.markdown("#### Variáveis Auxiliares")
        auxiliary_vars = selected_config_details.get("auxiliary_variables", [])
        if auxiliary_vars:
            st.write(", ".join(auxiliary_vars))
        else:
            st.write("Nenhuma variável auxiliar definida.")

        
        if st.button("Ativar Configuração"):
            st.session_state["config"] = selected_config_details
            st.success(f"A configuração '{selected_config}' foi ativada com sucesso!")

def configure_series():
    st.write("### Configurar Série a partir da Planilha")
    register_serie()
    st.write("### Selecionar Configuração de Série")
    select_config()

    
    