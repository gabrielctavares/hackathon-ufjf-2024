import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from database_service import load_data, update_data, update_row
import altair as alt


def show_visualization():
    st.write("### Dados no Banco de Dados")
    raca_filter = st.selectbox("Filtrar por raça", ["Todas"] + list(load_data()["raca"].unique()))
    semana_filter = st.slider("Filtrar por semana", min_value=1, max_value=52, value=(1, 52))

    filtered_data = load_data()
    if raca_filter != "Todas":
        filtered_data = filtered_data[filtered_data["raca"] == raca_filter]
    filtered_data = filtered_data[(filtered_data["semana"] >= semana_filter[0]) & (filtered_data["semana"] <= semana_filter[1])]

    if filtered_data.empty:
        st.warning("Nenhum dado cadastrado ainda.")
    else:
        show_grid(filtered_data)
        show_graph(filtered_data)
       

def show_grid(data): 
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_column("id", editable=False, header_name="Código")
    gb.configure_column("semana", editable=False, header_name="Semana")
    gb.configure_column("raca", editable=False, header_name="Raça")
    gb.configure_column("producao_kg", editable=True, header_name="Produção (kg)")
    gb.configure_column("anomalia", editable=True, header_name="Anomalia")  
    gb.configure_column("correcao_sugerida", editable=False, header_name="Correção Sugerida")
    grid_options = gb.build()

    grid_response = AgGrid(
        data,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        theme="streamlit",
    )

    updated_data = grid_response["data"]
    changes_detected = not data.equals(pd.DataFrame(updated_data))

    if changes_detected:
        st.warning("Alterações detectadas. Clique em 'Salvar Alterações' para confirmar.")
        if st.button("Salvar Alterações"):
            update_data(updated_data)

def show_graph(data):
    st.write("### Gráfico de Produção com Detecção de Anomalias")
    filtered_data = data[data["anomalia"] == False]
    anomalias = data[data["anomalia"] == True]

    mark_line = alt.Chart(filtered_data).mark_line(point=True).encode(
        x=alt.X("semana:O", title="Semana de Lactação"),
        y=alt.Y("producao_kg:Q", title="Produção de Leite (kg)"),
        color=alt.Color("raca:N", title="Raça"),  
        tooltip=[
            alt.Tooltip("id:O", title="ID"),
            alt.Tooltip("semana:O", title="Semana"),
            alt.Tooltip("raca:N", title="Raça"),
            alt.Tooltip("producao_kg:Q", title="Produção (kg)"),          
        ],
    )

    mark_point = alt.Chart(anomalias).mark_point(filled=True, size=150).encode(
        x="semana:O",
        y="producao_kg:Q",
        color=alt.value("red"),
        shape=alt.ShapeValue("circle"),  
        tooltip=[
            alt.Tooltip("id:O", title="ID"),
            alt.Tooltip("semana:O", title="Semana"),
            alt.Tooltip("raca:N", title="Raça"),
            alt.Tooltip("producao_kg:Q", title="Produção (kg)"),
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
        selected_id = st.selectbox(
            "Selecione o ID do valor anômalo que deseja corrigir:",
            anomalias["id"],
        )

        if selected_id:
            selected_row = anomalias[anomalias["id"] == selected_id]

            if not selected_row.empty:
                st.write(f"**Editar Produção do ID {selected_id}**")

                selected_row = selected_row.iloc[0].to_dict()    
                current_value = selected_row["producao_kg"]
                suggested_value = selected_row.get("correcao_sugerida")

                # Mostrar o valor atual e a sugestão de correção
                st.write(f"Valor atual: {current_value} kg")
                if pd.notna(suggested_value):
                    st.write(f"Correção sugerida: {suggested_value} kg")

                # Inputs para correção
                new_value = st.number_input(
                    "Novo valor de Produção (kg):",
                    min_value=0.0,
                    value=suggested_value if pd.notna(suggested_value) else current_value,
                    step=0.1,
                )

                selected_row["producao_kg"] = new_value

                if st.button("Salvar Correção"):               
                    update_data(pd.DataFrame([selected_row]))
                
    
    
    
    

