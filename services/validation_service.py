import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import IsolationForest


def detect_anomalies_with_prediction(data, new_entry, config):
    
    auxiliary_variables = config.get("auxiliary_variables", [])
    analysis_variable = config["analysis_variable"]
    series_column = config["series_column"]

    categorical_columns = data[auxiliary_variables].select_dtypes(include=["object", "category"]).columns.tolist() # Valores que precisam ser codificados


    contamination = config.get("contamination", 0.005)
    contamination = round(min(max(contamination, 0.005), 0.5), 3)  

    data_encoded = data[data["anomalia"] == False]
    data_encoded = pd.get_dummies(data_encoded, columns=categorical_columns, drop_first=False)
    new_entry_encoded = pd.get_dummies(new_entry, columns=categorical_columns, drop_first=False)


    for col in data_encoded.columns:
        if col not in new_entry_encoded.columns:
            new_entry_encoded[col] = 0

    dummy_columns = [col for col in data_encoded.columns if col.startswith(tuple(categorical_columns))]
    features = [series_column] + auxiliary_variables + dummy_columns

    def detect_anomalies(data_encoded, new_entry_encoded):
        anomaly_features = features + [analysis_variable] 
        
        if not all(field in data_encoded.columns for field in anomaly_features):
            raise ValueError("Dados incompletos para a detecção de anomalias.")

        X = data_encoded[anomaly_features]
        X = X.rename(str, axis="columns")

        new_entry_encoded = new_entry_encoded[X.columns]
        new_entry_encoded = new_entry_encoded.fillna(0)  
        new_entry_encoded = new_entry_encoded.rename(str, axis="columns")

        isolation_model = IsolationForest(contamination=contamination, random_state=42)
        isolation_model.fit(X)
        anomaly_score = isolation_model.decision_function(new_entry_encoded)
        is_anomaly = anomaly_score[0] < 0  
        return is_anomaly
    
    def predict_value(data_encoded, new_entry_encoded):        
        if not all(field in data_encoded.columns for field in features):
            raise ValueError("Dados incompletos para a predição.")

        X = data_encoded[features]
        y = data_encoded[analysis_variable]
        X = X.rename(str, axis="columns")

        regressor = RandomForestRegressor(random_state=42)
        regressor.fit(X, y)
        new_entry_encoded = new_entry_encoded[X.columns]
        new_entry_encoded = new_entry_encoded.rename(str, axis="columns")

        predicted_value = regressor.predict(new_entry_encoded)[0]
        return round(predicted_value, 2)

   
    is_anomaly = detect_anomalies(data_encoded, new_entry_encoded.copy())
    predicted_value = predict_value(data_encoded, new_entry_encoded.copy())
                                    
    return is_anomaly, predicted_value

def validate_and_suggest(data, new_entries: pd.DataFrame, config: dict):    
    anomalias, correcao_sugerida = [], []

    validations = config.get("validations", {})
    min_value = validations.get("min_value", None)
    max_value = validations.get("max_value", None)
    validate_mean = validations.get("validate_mean", False)
    mean_threshold = validations.get("mean_threshold", 20) / 100  
    validate_last = validations.get("validate_last", False)
    last_threshold = validations.get("last_threshold", 40) / 100  

    analysis_variable = config["analysis_variable"]
    series_column = config["series_column"]

    for _, row in new_entries.iterrows():
        race = row[series_column]
        value = row[analysis_variable]

        previous_data = data[data["anomalia"] == False]
        previous_data = previous_data[previous_data[series_column] == race]

        is_valid = True

        # 1. Validar valores mínimos e máximos
        if min_value is not None and value < min_value:
            is_valid = False
        if max_value is not None and value > max_value:
            is_valid = False

        # 2. Validar relação com a média dos valores anteriores
        if validate_mean and not previous_data.empty:
            mean_value = previous_data[analysis_variable].mean()
            if value > mean_value * (1 + mean_threshold):
                is_valid = False

        # 3. Validar relação com o último valor lançado
        if validate_last and not previous_data.empty:
            last_value = previous_data.sort_values("id").iloc[-1][analysis_variable]
            if value > last_value * (1 + last_threshold):
                is_valid = False

        # 4. IA: Detectar anomalias e sugerir valores
        is_anomaly_ia, suggested_value = detect_anomalies_with_prediction(data, pd.DataFrame([row]), config)

        is_anomaly = not is_valid or is_anomaly_ia
        anomalias.append(is_anomaly)
        correcao_sugerida.append(suggested_value if is_anomaly else None)

        print(f"Validado: {is_valid}, Validado por IA: {not is_anomaly_ia}")

        is_anomaly = not is_valid or is_anomaly_ia
        anomalias.append(is_anomaly)
        correcao_sugerida.append(suggested_value if is_anomaly else None)

    new_entries["anomalia"] = anomalias
    new_entries["correcao_sugerida"] = correcao_sugerida

    return new_entries
