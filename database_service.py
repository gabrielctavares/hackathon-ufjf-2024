import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from validation_service import validate_and_suggest


# Configurar banco de dados SQLite
DATABASE_URL = "sqlite:///lactacao.db"
engine = create_engine(DATABASE_URL)
metadata = MetaData()


# Tabela no banco de dados
lactacao_table = Table(
    "lactacao",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("semana", Integer),
    Column("raca", String),
    Column("producao_kg", Float),
    Column("anomalia", Boolean, default=False),
    Column("correcao_sugerida", Float, nullable=True),    
)

metadata.create_all(engine)

# Function to load defaults into the database
@st.cache_data
def load_defaults(file_path):
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM lactacao")).fetchone()[0]
        if count == 0:
            data = pd.read_csv(file_path)
            data["anomalia"] = False
            data["correcao_sugerida"] = None
            data.to_sql("lactacao", conn, if_exists="append", index=False)
            conn.commit()
            st.success("Base de conhecimento carregada com sucesso!")

file_path = 'Lactacao (2).csv'
# Call the load_defaults function on app startup
load_defaults(file_path)



# Função para carregar dados do banco
def load_data():
    try: 
        with engine.connect() as conn:
            return pd.read_sql(lactacao_table.select(), conn)
    except SQLAlchemyError as e:
        st.error(f"Erro ao buscar dados: {e}")

def update_data(updated_data):
    try:
        # Save the changes to the database
        with engine.connect() as conn:
            for _, row in updated_data.iterrows():                
                row = validate_data(row)
                stmt = (
                    update(lactacao_table)
                    .where(lactacao_table.c.id == row["id"]) 
                    .values(
                        semana=row["semana"],
                        raca=row["raca"],
                        producao_kg=row["producao_kg"],
                        anomalia=row["anomalia"],
                        correcao_sugerida=row["correcao_sugerida"],
                    )
                )
                conn.execute(stmt)
            conn.commit()
            
        st.success("Alterações salvas no banco de dados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar alterações: {e}")       

def update_row(row):
    try:        
        row = validate_data(row)
        with engine.connect() as conn:
            stmt = (
                update(lactacao_table)
                .where(lactacao_table.c.id == row["id"]) 
                .values(
                    semana=row["semana"],
                    raca=row["raca"],
                    producao_kg=row["producao_kg"],
                    anomalia=row["anomalia"],
                    correcao_sugerida=row["correcao_sugerida"],
                )
            )
            conn.execute(stmt)
            conn.commit()
        st.success("Alterações salvas no banco de dados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar alterações: {e}")

def save_data(data):    
    try:
        if isinstance(data, pd.DataFrame):
            validated_data = validate_data(data)
        else:
            validated_data = validate_data(pd.DataFrame([data]))
        
        if validated_data.empty:
            st.warning("Nenhum dado validado para salvar.")
            return
        
        with engine.connect() as conn:
            conn.execute(lactacao_table.insert(), validated_data.to_dict(orient="records"))
            conn.commit()
        st.success("Dados validados e salvos com sucesso!")
    except SQLAlchemyError as e:
        st.error(f"Erro ao salvar dados: {e}")

def validate_data(data):
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame([data])

    existing_data = load_data()
    validated_data = validate_and_suggest(existing_data, data)

    return validated_data