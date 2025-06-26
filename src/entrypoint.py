import json
import mlflow
import os
import pandas as pd
import numpy as np

user = "grupo5"
model_name = f"model-attrition-{user}"
model_version = "latest"
model_uri = f"models:/{model_name}/{model_version}"


def lambda_handler(event, context):
  try:
    os.environ['MLFLOW_TRACKING_USERNAME'] = 'name'
    os.environ['MLFLOW_TRACKING_PASSWORD'] = 'pass'

    tracking_uri = os.environ['MLFLOW_TRACKING_SERVER_ARN']
    print(f"Tracking URI: {tracking_uri}")

    # Configuración básica
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow tracking URI set to: {tracking_uri}")

    model = mlflow.xgboost.load_model(model_uri)

    # Procesamiento simple
    input_data = json.loads(event['body']).get('input_data', {})
    print(f"Received input data: {input_data}")

    data = pd.DataFrame({
        # Variables numéricas originales
        'flg_bancarizado': [1],
        'edad': [35.0],
        'antiguedad': [5.0],
        'sdo_activo_menos0': [15000],
        'sdo_activo_menos1': [12000],
        'sdo_activo_menos2': [10000],
        'flg_seguro_menos0': [1],
        'flg_seguro_menos1': [1],
        'flg_seguro_menos2': [0],
        'flg_nomina': [1],
        'nro_acces_canal1_menos0': [5],
        'nro_acces_canal2_menos0': [10],
        'nro_acces_canal3_menos0': [2],

        # Variables categóricas ya codificadas (valores numéricos)
        'flag_lima_provincia_encoded': [0],  # 0=Provincia, 1=Lima
        'rang_ingreso_encoded': [2],         # Valor numérico del encoder
        'rang_sdo_pasivo_menos0_encoded': [1]  # Valor numérico del encoder
    })

    # Ejecutar predicción
    pred = model.predict_proba(data)[:, 1][0]

    # Tracking con MLflow
    # with mlflow.start_run():
    #   mlflow.log_param("input", str(input_data))
    #   mlflow.log_metric("requests", 1)
    #   print("done...")

    print("MLflow parameters and metrics logged.")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Éxito', 'pred': pred})
    }
  except Exception as e:
    print(f"Error in lambda_handler: {e}")

    return {
        'statusCode': 500,
        'body': json.dumps({'message': 'Error', 'error': str(e)})
    }
