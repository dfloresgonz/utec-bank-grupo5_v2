import json
import boto3
import mlflow
import os


def lambda_handler(event, context):
  try:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

    print(f"Tracking URI: {tracking_uri}")
    print(f"Tracking Server ARN: {tracking_server_arn}")

    # Configurar credentials explícitamente
    session = boto3.Session()
    credentials = session.get_credentials()

    # Set environment variables for MLflow
    os.environ['MLFLOW_TRACKING_SERVER_ARN'] = tracking_server_arn
    os.environ['AWS_ACCESS_KEY_ID'] = credentials.access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = credentials.secret_key
    if credentials.token:
      os.environ['AWS_SESSION_TOKEN'] = credentials.token

    # Verificar permisos SageMaker primero
    try:
      sagemaker_client = boto3.client('sagemaker')
      server_info = sagemaker_client.describe_mlflow_tracking_server(
          TrackingServerName=tracking_server_arn.split('/')[-1]
      )
      print(
          f"MLflow server status: {server_info.get('TrackingServerStatus', 'Unknown')}")
    except Exception as sm_error:
      print(f"SageMaker access error: {sm_error}")
      # Continue anyway, might still work

    body = json.loads(event['body'])
    input_data = body.get('input_data')
    print(f"body: {body}")

    # Configure MLflow
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow tracking URI set to: {mlflow.get_tracking_uri()}")

    # Create or get experiment
    experiment_name = "lambda-experiment"
    try:
      experiment_id = mlflow.create_experiment(experiment_name)
      print(f"Created experiment: {experiment_id}")
    except:
      experiment = mlflow.get_experiment_by_name(experiment_name)
      experiment_id = experiment.experiment_id if experiment else None
      print(f"Using existing experiment: {experiment_id}")

    # Log to MLflow
    with mlflow.start_run(experiment_id=experiment_id):
      print("Starting MLflow run")
      mlflow.log_param("input_data", str(input_data))
      mlflow.log_param("lambda_request_id", context.aws_request_id)
      print("Successfully logged to MLflow")

    result = {
        "message": "Successfully processed and logged to MLflow",
        "input_data": input_data
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'result': result})
    }

  except Exception as e:
    print(f"Error occurred: {str(e)}")
    return {
        'statusCode': 500,
        'body': json.dumps({'error': str(e)})
    }
