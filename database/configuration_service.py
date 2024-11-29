# configuration_service.py
from sqlalchemy import Float, Table, Column, Integer, String, JSON, insert, select
from database.database_config import metadata, engine

# Tabela de Configurações
configuracoes_table = Table(
    "configuracoes_serie",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nome_serie", String, nullable=False, unique=True),
    Column("series_column", String, nullable=False),
    Column("analysis_variable", String, nullable=False),
    Column("auxiliary_variables", JSON, nullable=True),
    Column("filters", JSON, nullable=True),
    Column("validations", JSON, nullable=True),
    Column("dynamic_table_name", String, nullable=False),
    Column("contamination", Float, nullable=False),    
)

metadata.create_all(engine)

def save_configuration(config):
    try:
    
        with engine.connect() as conn:
            stmt = insert(configuracoes_table).values(config)
            conn.execute(stmt)
            conn.commit()
            return True
    except Exception as e:        
        conn.rollback()
        return False

def get_configuration(nome_serie):
    with engine.connect() as conn:
        stmt = select(configuracoes_table).where(configuracoes_table.c.nome_serie == nome_serie)
        result = conn.execute(stmt).fetchone()
    if result:
        return dict(result)
    return None

def get_all_configurations():
    with engine.connect() as conn:
        stmt = select(configuracoes_table)
        result = conn.execute(stmt).fetchall()
    return [dict(row._mapping) for row in result]