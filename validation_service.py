import pandas as pd
import numpy as np

from scipy.optimize import curve_fit

from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

# Função da curva de Wood
def wood_curve(t, a, b, c):
    """
    Modelo de Wood para curvas de lactação.
    Args:
        t (float): Semana de lactação.
        a (float): Parâmetro de produção inicial.
        b (float): Parâmetro de inclinação na fase ascendente.
        c (float): Parâmetro de declínio após o pico.
    Returns:
        float: Produção esperada na semana t.
    """
    return a * (t**b) * np.exp(-c * t)

def get_expected_production(data, race, week=None):
    race_data = data[data["raca"] == race]
    
    if race_data.empty:
        return None  # Sem dados para ajustar a curva

    initial_a = race_data[race_data["semana"] <= 4]["producao_kg"].mean()  # Produção média no início
    initial_b = 0.2
    initial_c = 0.02

    params, _ = curve_fit(wood_curve, race_data["semana"], race_data["producao_kg"], p0=[initial_a, initial_b, initial_c], maxfev=10000)
    a, b, c = params

    expected_production = wood_curve(week, a, b, c)
    return round(expected_production, 2)

# Regra da Curva 
def validate_curve(value, data, race, week=None):
    expected_production = get_expected_production(data, race, week)
    
    if expected_production is None:
        return True  # Sem curva disponível, nenhuma validação    

    print(f"Esperado: {expected_production}, Valor: {value}")
    return value <= expected_production * 1.5  # Não exceder 50% da curva

# Regra da Média
def validate_mean(value, previous_data):    
    if previous_data.empty:
        return True  # Sem histórico, nenhuma validação
    
    mean_value = round(previous_data["producao_kg"].mean(), 2)

    print(f"Média: {mean_value}, Valor: {value}")
    return value <= mean_value * 1.2  # Não exceder 20% da média

# Regra do Último Valor
def validate_last_value(value, previous_data):
    previous_data = previous_data[previous_data["anomalia"] == False]

    if previous_data.empty:
        return True  # Sem histórico, nenhuma validação
    
    last_value = previous_data.sort_values("id").iloc[-1]["producao_kg"]

    print(f"Último: {last_value}, Valor: {value}")
    return value <= last_value * 1.4  # Não exceder 40% do último valor

# Detectar anomalias e prever um valor apropriado
def detect_anomalies_with_prediction(data, new_entry):
    data_encoded = data[data["anomalia"] == False]
    data_encoded = pd.get_dummies(data_encoded, columns=["raca"], drop_first=False)
    new_entry_encoded = pd.get_dummies(new_entry, columns=["raca"], drop_first=False)

    for col in data_encoded.columns:
        if col not in new_entry_encoded.columns:
            new_entry_encoded[col] = 0

    def detect_anomalies(data_encoded, new_entry_encoded):
        anomaly_features = ["producao_kg", "semana"] + [col for col in data_encoded.columns if col.startswith("raca_")]
        
        if not all(field in data_encoded.columns for field in anomaly_features):
            raise ValueError("Dados incompletos para a detecção de anomalias.")

        X = data_encoded[anomaly_features]
        X = X.rename(str, axis="columns")

        new_entry_encoded = new_entry_encoded[X.columns]
        new_entry_encoded = new_entry_encoded.fillna(0)  
        new_entry_encoded = new_entry_encoded.rename(str, axis="columns")
        

        contamination = len(data[data["anomalia"] == True]) / len(data)
        contamination = min(max(contamination, 0.005), 0.5)  

        print(f"Contaminação: {contamination}")

        isolation_model = IsolationForest(contamination=contamination, random_state=42)
        isolation_model.fit(X)
        print("Passou aqui 1")
        anomaly_score = isolation_model.decision_function(new_entry_encoded)
        is_anomaly = anomaly_score[0] < 0  
        return is_anomaly
    
    def predict_value(data_encoded, new_entry_encoded):
        features = ["semana"] + [col for col in data_encoded.columns if col.startswith("raca_")]
        
        if not all(field in data_encoded.columns for field in features):
            raise ValueError("Dados incompletos para a predição.")

        X = data_encoded[features]
        y = data_encoded["producao_kg"]
        X = X.rename(str, axis="columns")

        regressor = RandomForestRegressor(random_state=42)
        regressor.fit(X, y)
        new_entry_encoded = new_entry_encoded[X.columns]
        new_entry_encoded = new_entry_encoded.rename(str, axis="columns")

        predicted_value = regressor.predict(new_entry_encoded)[0]
        return round(predicted_value, 2)

   
    is_anomaly = detect_anomalies(data_encoded, new_entry_encoded.copy())
    print("é anomalia", is_anomaly)
    predicted_value = predict_value(data_encoded, new_entry_encoded.copy())
                                    
    return is_anomaly, predicted_value

def validate_and_suggest(data, new_entries: pd.DataFrame):    
    anomalias = []
    correcao_sugerida = []

    for _, row in new_entries.iterrows():
        race = str(row["raca"])
        week = row.get("semana", None)

        previous_data = data[data["anomalia"] == False]
        previous_data = data[data["raca"] == race]
        if week is not None:
            previous_data = previous_data[previous_data["semana"] == int(week)]

        is_curve_valid = validate_curve(row["producao_kg"], data, race, week)
        is_mean_valid = validate_mean(row["producao_kg"], previous_data)
        is_last_valid = validate_last_value(row["producao_kg"], previous_data)

        is_anomaly_ia, suggested_value = detect_anomalies_with_prediction(data, pd.DataFrame([row]))

        is_valid = is_curve_valid and is_mean_valid and is_last_valid

        print(f"Curva: {is_curve_valid}, Média: {is_mean_valid}, Último: {is_last_valid}, IA: {not is_anomaly_ia}")

        is_anomaly = not is_valid or is_anomaly_ia
        anomalias.append(is_anomaly)
        correcao_sugerida.append(suggested_value if is_anomaly else None)

    new_entries["anomalia"] = anomalias
    new_entries["correcao_sugerida"] = correcao_sugerida

    return new_entries
