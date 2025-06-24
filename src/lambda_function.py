import json
import mlflow
import os


def lambda_handler(event, context):
  tracking_uri = os.environ['MLFLOW_TRACKING_URI']
  print(f"Tracking URI: {tracking_uri}")
  # Configuración básica
  mlflow.set_tracking_uri(tracking_uri)

  # Procesamiento simple
  input_data = json.loads(event['body']).get('input_data', {})

  # Tracking con MLflow
  with mlflow.start_run():
    mlflow.log_param("input", str(input_data))
    mlflow.log_metric("requests", 1)

  return {
      'statusCode': 200,
      'body': json.dumps({'message': 'Éxito', 'input': input_data})
  }
