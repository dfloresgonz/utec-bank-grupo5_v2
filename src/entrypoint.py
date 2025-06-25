import json
import mlflow
import os

os.environ['MLFLOW_TRACKING_USERNAME'] = 'name'
os.environ['MLFLOW_TRACKING_PASSWORD'] = 'pass'
# tracking_uri = os.environ['MLFLOW_TRACKING_URI']
tracking_uri = os.environ['MLFLOW_TRACKING_SERVER_ARN']
print(f"Tracking URI: {tracking_uri}")
# Configuración básica
mlflow.set_tracking_uri(tracking_uri)
print(f"MLflow tracking URI set to: {tracking_uri}")


def lambda_handler(event, context):

  # Procesamiento simple
  input_data = json.loads(event['body']).get('input_data', {})
  print(f"Received input data: {input_data}")

  # Tracking con MLflow
  with mlflow.start_run():
    mlflow.log_param("input", str(input_data))
    mlflow.log_metric("requests", 1)
    print("done...")

  print("MLflow parameters and metrics logged.")

  return {
      'statusCode': 200,
      'body': json.dumps({'message': 'Éxito', 'input': input_data})
  }
