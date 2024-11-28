
# Treinar o modelo de IA
import pickle
from sklearn.ensemble import IsolationForest
import streamlit as st


# Caminho para salvar o modelo treinado
MODEL_PATH = "modelo_isolation_forest.pkl"


def train_model(data):
    features = ["producao_kg", "semana", "media_anterior", "ultimo_valor"]
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(data[features].dropna())
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model



# Inferência com o modelo de IA
def infer_with_model(data):
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    except FileNotFoundError:
        st.error("Modelo não encontrado. Treine o modelo primeiro!")
        return data
    features = ["producao_kg", "semana", "media_anterior", "ultimo_valor"]
    data["anomalia_ia"] = model.predict(data[features].dropna()) == -1
    data["correcao_sugerida"] = data["producao_kg"].where(~data["anomalia_ia"], data["media_anterior"])
    return data
