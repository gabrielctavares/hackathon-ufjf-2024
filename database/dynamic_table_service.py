from sqlalchemy import Table, Column, Integer, String, Float, Boolean, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import MetaData
from sqlalchemy.engine import Engine
from database.database_config import metadata, engine
import pandas as pd
import streamlit as st

from services.validation_service import validate_and_suggest

def create_dynamic_table(table_name: str, dataframe: pd.DataFrame):
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("anomalia", Boolean, default=False),
        Column("correcao_sugerida", Float, nullable=True),
    ]

    for col in dataframe.columns:
        if pd.api.types.is_integer_dtype(dataframe[col]):
            column_type = Integer
        elif pd.api.types.is_float_dtype(dataframe[col]):
            column_type = Float
        elif pd.api.types.is_bool_dtype(dataframe[col]):
            column_type = Boolean
        else:
            column_type = String

        columns.append(Column(col, column_type))

    dynamic_table = Table(table_name, metadata, *columns)
    metadata.create_all(engine)
    return dynamic_table

def load_data(table_name: str):
    dynamic_table = Table(table_name, metadata, autoload_with=engine)
    try:
        with engine.connect() as conn:
            return pd.read_sql(dynamic_table.select(), conn)
    except SQLAlchemyError as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame() 

def save_data(table_name: str, dataframe: pd.DataFrame, config: dict):
    validated_data = validate_data(dataframe, table_name, config)
    dynamic_table = Table(table_name, metadata, autoload_with=engine)
    with engine.connect() as conn:
        conn.execute(dynamic_table.insert(), validated_data.to_dict(orient="records"))
        conn.commit()

def update_data(table_name: str, dataframe: pd.DataFrame, config: dict):
    validated_data = validate_data(dataframe, table_name, config)
    dynamic_table = Table(table_name, metadata, autoload_with=engine)
    
    with engine.connect() as conn:
        conn.execute(dynamic_table.update(), validated_data.to_dict(orient="records"))
        conn.commit()

def validate_data(data: pd.DataFrame, table_name: str, config: dict):
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame([data])

    existing_data = load_data(table_name)
    validated_data = validate_and_suggest(existing_data, data, config)
    return validated_data

def load_columns_info(table_name: str):
    inspector = inspect(engine)
    return inspector.get_columns(table_name)