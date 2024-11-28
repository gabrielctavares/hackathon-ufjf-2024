import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

def get_dynamic_curve(data, race, week=None):
    race_data = data[data["raca"] == race]
    if week is not None:
        race_data = race_data[race_data["semana"] == int(week)]

    if race_data.empty:
        return None
    
    return race_data["producao_kg"].mean()  

# Regra da Curva 
def validate_curve(value, data, race, week=None):
    curve = get_dynamic_curve(data, race, week)
    
    if curve is None:
        return True  # Sem curva disponível, nenhuma validação
    
    return value <= curve * 1.5  # Não exceder 50% acima da curva

# Regra da Média
def validate_mean(value, previous_data):
    if previous_data.empty:
        return True  # Sem histórico, nenhuma validação
    
    mean_value = previous_data["producao_kg"].mean()
    return value <= mean_value * 1.2  # Não exceder 20% da média

# Regra do Último Valor
def validate_last_value(value, previous_data):
    if previous_data.empty:
        return True  # Sem histórico, nenhuma validação
    
    last_value = previous_data.iloc[-1]["producao_kg"]
    return value <= last_value * 1.4  # Não exceder 40% do último valor

# Detectar anomalias e prever um valor apropriado
def detect_anomalies_with_prediction(data, new_entry):
    data_encoded = pd.get_dummies(data, columns=["raca"], drop_first=False)
    new_entry_encoded = pd.get_dummies(new_entry, columns=["raca"], drop_first=False)

    for col in data_encoded.columns:
        if col not in new_entry_encoded.columns:
            new_entry_encoded[col] = 0
   

    def detect_anomalies(data_encoded, new_entry_encoded):
        anomaly_features = ["producao_kg", "semana"] + [col for col in data_encoded.columns if col.startswith("raca_")]
        
        if not all(field in data_encoded.columns for field in anomaly_features):
            raise ValueError("Dados incompletos para a detecção de anomalias.")

        X = data_encoded[anomaly_features]

        new_entry_encoded = new_entry_encoded[X.columns]

        isolation_model = IsolationForest(contamination=0.05, random_state=42)
        isolation_model.fit(X.values)

        anomaly_score = isolation_model.decision_function(new_entry_encoded.values)
        is_anomaly = anomaly_score[0] < 0  

        return is_anomaly
    
    def predict_value(data_encoded, new_entry_encoded):
        features = ["semana"] + [col for col in data_encoded.columns if col.startswith("raca_")]        

        if not all(field in data_encoded.columns for field in features):
            raise ValueError("Dados incompletos para a predição.")
        
        X = data_encoded[features]
        y = data_encoded["producao_kg"]

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
        regressor = RandomForestRegressor(random_state=42)
        regressor.fit(X_train.values, y_train)
              
        new_entry_encoded = new_entry_encoded[X.columns]        
        predicted_value = regressor.predict(new_entry_encoded)[0]
        return round(predicted_value, 2)

   
    is_anomaly = detect_anomalies(data_encoded, new_entry_encoded)
    predicted_value = predict_value(data_encoded, new_entry_encoded)
                                    
    return is_anomaly, predicted_value

def validate_and_suggest(data, new_entry):
    if isinstance(new_entry, dict):
        new_entry = pd.DataFrame([new_entry])
    elif not isinstance(new_entry, pd.DataFrame):
        raise ValueError("`new_entry` deve ser um dicionário ou um DataFrame.")

    anomalias = []
    correcao_sugerida = []

    for _, row in new_entry.iterrows():
        race = str(row["raca"])
        week = row.get("semana", None)

        previous_data = data[data["raca"] == race]
        if week is not None:
            previous_data = previous_data[previous_data["semana"] <= int(week)]

        is_curve_valid = validate_curve(row["producao_kg"], data, race, week)
        is_mean_valid = validate_mean(row["producao_kg"], previous_data)
        is_last_valid = validate_last_value(row["producao_kg"], previous_data)

        is_anomaly_ia, suggested_value = detect_anomalies_with_prediction(data, row)

        is_valid = is_curve_valid and is_mean_valid and is_last_valid

        is_anomaly = not is_valid or is_anomaly_ia
        anomalias.append(is_anomaly)
        correcao_sugerida.append(suggested_value if is_anomaly else None)

    new_entry["anomalia"] = anomalias
    new_entry["correcao_sugerida"] = correcao_sugerida

    return new_entry
