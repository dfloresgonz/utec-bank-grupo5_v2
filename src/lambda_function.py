import json
import boto3
import os
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def lambda_handler(event, context):
  try:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

    print(f"Tracking URI: {tracking_uri}")
    print(f"Tracking Server ARN: {tracking_server_arn}")

    # Verificar el servidor SageMaker
    try:
      sagemaker_client = boto3.client('sagemaker')
      server_info = sagemaker_client.describe_mlflow_tracking_server(
          TrackingServerName=tracking_server_arn.split('/')[-1]
      )
      print(
          f"MLflow server status: {server_info.get('TrackingServerStatus', 'Unknown')}")
    except Exception as sm_error:
      print(f"SageMaker access error: {sm_error}")

    body = json.loads(event['body'])
    input_data = body.get('input_data')
    print(f"body: {body}")

    # Usar requests directamente con AWS Auth
    session = boto3.Session()
    credentials = session.get_credentials()

    # Preparar headers AWS para MLflow API
    def make_mlflow_request(endpoint, method='GET', data=None):
      url = f"{tracking_uri}/api/2.0/mlflow/{endpoint}"

      # Crear la request AWS
      request = AWSRequest(method=method, url=url, data=data)
      request.headers['X-Amz-Tracking-Server-Arn'] = tracking_server_arn
      if data:
        request.headers['Content-Type'] = 'application/json'

      # Firmar la request
      SigV4Auth(credentials, 'sagemaker',
                session.region_name).add_auth(request)

      # Hacer la request
      response = requests.request(
          method=method,
          url=url,
          headers=dict(request.headers),
          data=data,
          timeout=30
      )
      return response

    # Test: Listar experimentos
    try:
      response = make_mlflow_request('experiments/list')
      print(f"Experiments list response: {response.status_code}")
      if response.status_code == 200:
        experiments = response.json()
        print(f"Found {len(experiments.get('experiments', []))} experiments")
      else:
        print(f"Error response: {response.text}")
    except Exception as exp_error:
      print(f"Experiments list error: {exp_error}")

    # Test: Crear un experimento
    experiment_name = "lambda-test-experiment"
    experiment_data = {
        "name": experiment_name,
        "artifact_location": f"s3://s3-mlflow-artifacts-mlflow-tracking-server-grupo5-01/mlflow-artifacts/{experiment_name}"
    }

    try:
      response = make_mlflow_request(
          'experiments/create', 'POST', json.dumps(experiment_data))
      print(f"Create experiment response: {response.status_code}")
      if response.status_code == 200:
        experiment_result = response.json()
        experiment_id = experiment_result.get('experiment_id')
        print(f"Created experiment ID: {experiment_id}")
      else:
        print(f"Create experiment error: {response.text}")
        # Intentar obtener experimento existente
        response = make_mlflow_request(
            f'experiments/get-by-name?experiment_name={experiment_name}')
        if response.status_code == 200:
          experiment_result = response.json()
          experiment_id = experiment_result.get(
              'experiment', {}).get('experiment_id', '0')
          print(f"Using existing experiment ID: {experiment_id}")
        else:
          experiment_id = '0'  # Default experiment
    except Exception as create_error:
      print(f"Create experiment error: {create_error}")
      experiment_id = '0'

    # Test: Crear un run
    run_data = {
        "experiment_id": experiment_id,
        # Current timestamp in milliseconds
        "start_time": int(1000 * 1719213814),
        "tags": [
            {"key": "lambda_request_id", "value": context.aws_request_id},
            {"key": "input_data", "value": str(input_data)}
        ]
    }

    try:
      response = make_mlflow_request(
          'runs/create', 'POST', json.dumps(run_data))
      print(f"Create run response: {response.status_code}")
      if response.status_code == 200:
        run_result = response.json()
        run_id = run_result.get('run', {}).get('info', {}).get('run_id')
        print(f"Created run ID: {run_id}")

        # Log parameter
        param_data = {
            "run_id": run_id,
            "key": "input_data",
            "value": str(input_data)
        }
        param_response = make_mlflow_request(
            'runs/log-parameter', 'POST', json.dumps(param_data))
        print(f"Log parameter response: {param_response.status_code}")

      else:
        print(f"Create run error: {response.text}")
    except Exception as run_error:
      print(f"Create run error: {run_error}")

    result = {
        "message": "MLflow API test completed",
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
