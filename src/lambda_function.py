import json
import boto3
import mlflow
import os
from mlflow.tracking import MlflowClient


def lambda_handler(event, context):
  try:
    # Initialize the MLflow tracking URI
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

    print(f"Tracking URI: {tracking_uri}")
    print(f"Tracking Server ARN: {tracking_server_arn}")

    # Configurar autenticación AWS
    session = boto3.Session()
    credentials = session.get_credentials()

    # Configurar variables de entorno para MLflow
    os.environ['MLFLOW_TRACKING_SERVER_ARN'] = tracking_server_arn
    os.environ['AWS_ACCESS_KEY_ID'] = credentials.access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = credentials.secret_key
    if credentials.token:
      os.environ['AWS_SESSION_TOKEN'] = credentials.token

    body = json.loads(event['body'])
    input_data = body.get('input_data')
    print(f"body: {body}")

    # Configurar MLflow
    mlflow.set_tracking_uri(tracking_uri)
    print("after setting tracking URI")
    print(f"MLflow tracking URI set to: {mlflow.get_tracking_uri()}")

    # Crear cliente MLflow con autenticación
    client = MlflowClient(tracking_uri=tracking_uri)
    print("MLflow client created")

    # Intentar crear experimento o usar existente
    experiment_name = "lambda-test"
    try:
      experiment_id = mlflow.create_experiment(experiment_name)
      print(f"Created experiment: {experiment_id}")
    except Exception as exp_error:
      print(f"Experiment creation error: {exp_error}")
      try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        experiment_id = experiment.experiment_id if experiment else None
        print(f"Using existing experiment: {experiment_id}")
      except:
        experiment_id = None
        print("Using default experiment")

    # Hacer logging
    with mlflow.start_run(experiment_id=experiment_id):
      print("Starting MLflow run")
      mlflow.log_param("input_data", str(input_data))
      mlflow.log_param("lambda_request_id", context.aws_request_id)
      print("Successfully logged parameters")

    print("after logging input data")
    result = {
        "message": "This is a mock response for input",
        "input_data": input_data
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'result': result})
    }

  except Exception as e:
    print(f"Error occurred: {str(e)}")
    print(f"Error type: {type(e)}")
    return {
        'statusCode': 500,
        'body': json.dumps({'error': str(e)})
    }
