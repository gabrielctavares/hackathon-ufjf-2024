import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from database.dynamic_table_service import load_data, update_data
import altair as alt


def show_visualization():
    config = st.session_state.get("config", {})
    if not config:
        st.warning("Nenhuma configuração de série carregada.")
        return

    st.write(f"### Dados da Série: {config['nome_serie']}")

    table_name = config["dynamic_table_name"]
    data = load_data(table_name)

    filters = configure_filters(data, config)
    filtered_data = apply_filters(data, filters)

    if filtered_data.empty:
        st.warning("Nenhum dado cadastrado ainda com os filtros aplicados.")
    else:
        show_grid(filtered_data, config)
        show_graph(filtered_data, config)


def configure_filters(data, config):
    filters = {}
    for col in data.columns:
        if col in ["id", "anomalia", "correcao_sugerida"]:  
            continue

        if col == config["analysis_variable"]:  
            continue

        if pd.api.types.is_numeric_dtype(data[col]):
            if pd.api.types.is_integer_dtype(data[col]):
                min_value, max_value = int(data[col].min()), int(data[col].max())
            else:
                min_value, max_value = float(data[col].min()), float(data[col].max())
            filters[col] = st.slider(
                f"Filtrar por {col} (intervalo)",
                min_value=min_value,
                max_value=max_value,
                value=(min_value, max_value),
            )
        else:
            unique_values = data[col].unique()
            filters[col] = st.multiselect(f"Filtrar por {col}", options=unique_values, default=unique_values)

    return filters


def apply_filters(data, filters):
    filtered_data = data.copy()
    for col, condition in filters.items():
        if isinstance(condition, tuple):  
            filtered_data = filtered_data[(filtered_data[col] >= condition[0]) & (filtered_data[col] <= condition[1])]
        elif isinstance(condition, list): 
            if condition:
                filtered_data = filtered_data[filtered_data[col].isin(condition)]

    return filtered_data


def show_grid(data, config):
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_column("id", editable=False, header_name="Código")
    
    for col in data.columns:
        if col not in ["id", "anomalia", "correcao_sugerida"]:
            gb.configure_column(col, editable=col == config["analysis_variable"], header_name=col.capitalize())
    
    gb.configure_column("anomalia", editable=False, header_name="Anomalia")
    gb.configure_column("correcao_sugerida", editable=False, header_name="Correção Sugerida")

    grid_options = gb.build()
    grid_response = AgGrid(
        data,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        theme="streamlit",
    )

    updated_data = grid_response["data"]
    changes_detected = data.compare(updated_data)

    if not changes_detected.empty:
        st.warning("Alterações detectadas. Clique em 'Salvar Alterações' para confirmar.")
        if st.button("Salvar Alterações"):
            altered_rows = updated_data.loc[changes_detected.index]
            update_data(config["dynamic_table_name"], altered_rows)


def show_graph(data, config):
    st.write(f"### Gráfico de {config['analysis_variable']} com Detecção de Anomalias")
    filtered_data = data[data["anomalia"] == False]
    anomalias = data[data["anomalia"] == True]

    mark_line = alt.Chart(filtered_data).mark_line(point=True).encode(
        x=alt.X(config["series_column"] + ":O", title=config["series_column"].capitalize()),
        y=alt.Y(config["analysis_variable"] + ":Q", title=config["analysis_variable"].capitalize()),
        color=alt.Color(config["auxiliary_variables"][0] + ":N", title=config["auxiliary_variables"][0].capitalize())
        if config["auxiliary_variables"]
        else alt.value("blue"),
        tooltip=[
            alt.Tooltip("id:O", title="ID"),
            alt.Tooltip(config["series_column"] + ":O", title=config["series_column"]),
            alt.Tooltip(config["analysis_variable"] + ":Q", title=config["analysis_variable"]),
        ],
    )

    mark_point = alt.Chart(anomalias).mark_point(filled=True, size=150).encode(
        x=config["series_column"] + ":O",
        y=config["analysis_variable"] + ":Q",
        color=alt.value("red"),
        tooltip=[
            alt.Tooltip("id:O", title="ID"),
            alt.Tooltip(config["series_column"] + ":O", title=config["series_column"]),
            alt.Tooltip(config["analysis_variable"] + ":Q", title=config["analysis_variable"]),
            alt.Tooltip("correcao_sugerida:Q", title="Correção Sugerida"),
        ],
    )

    graph = mark_line + mark_point
    graph = graph.properties().configure_legend(
        titleFontSize=14,
        labelFontSize=12,
    ).interactive()

    st.altair_chart(graph, use_container_width=True)

    if not anomalias.empty:
        analysis_variable = config["analysis_variable"]

        selected_id = st.selectbox(
            "Selecione o ID do valor anômalo que deseja corrigir:",
            options=anomalias["id"],
            format_func=lambda x: f"ID {x}"
        )

        if selected_id:
            selected_row = anomalias[anomalias["id"] == selected_id].iloc[0]
            
            st.write(f"**Editar {analysis_variable.capitalize()} do ID {selected_id}**")

            current_value = selected_row[analysis_variable]
            suggested_value = selected_row.get("correcao_sugerida", None)

            st.write(f"**Valor atual:** {current_value}")
            if pd.notna(suggested_value):
                st.write(f"**Correção sugerida:** {suggested_value}")

            new_value = st.number_input(
                f"Novo valor para {analysis_variable.capitalize()}:",
                min_value=0.0,
                value=suggested_value if pd.notna(suggested_value) else current_value,
                step=0.1,
                format="%.2f"
            )

            if st.button("Salvar Correção"):
                selected_row = selected_row.to_dict()  
                selected_row[analysis_variable] = new_value                
                update_data(config["dynamic_table_name"], pd.DataFrame([selected_row]))
                st.success(f"Correção do ID {selected_id} salva com sucesso!")
