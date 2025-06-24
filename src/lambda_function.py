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

    body = json.loads(event['body'])
    input_data = body.get('input_data')
    print(f"body: {body}")

    # Verificar acceso S3 ahora
    s3_client = boto3.client('s3')
    bucket_name = "s3-mlflow-artifacts-mlflow-tracking-server-grupo5-01"

    try:
      bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
      print(f"S3 access: SUCCESS - {bucket_location}")
    except Exception as s3_error:
      print(f"S3 access still failing: {s3_error}")
      return {
          'statusCode': 500,
          'body': json.dumps({'error': f'S3 access denied: {str(s3_error)}'})
      }

    # MLflow API con autenticación AWS
    session = boto3.Session()
    credentials = session.get_credentials()

    def make_mlflow_request(endpoint, method='GET', data=None):
      url = f"{tracking_uri}/api/2.0/mlflow/{endpoint}"
      request = AWSRequest(method=method, url=url, data=data)
      request.headers['X-Amz-Tracking-Server-Arn'] = tracking_server_arn
      if data:
        request.headers['Content-Type'] = 'application/json'

      SigV4Auth(credentials, 'sagemaker',
                session.region_name).add_auth(request)

      response = requests.request(
          method=method,
          url=url,
          headers=dict(request.headers),
          data=data,
          timeout=30
      )
      return response

    # Probar crear experimento
    experiment_name = "lambda-test-experiment"
    experiment_data = {
        "name": experiment_name,
        "artifact_location": f"s3://{bucket_name}/mlflow-artifacts/{experiment_name}"
    }

    response = make_mlflow_request(
        'experiments/create', 'POST', json.dumps(experiment_data))
    print(f"Create experiment response: {response.status_code}")

    if response.status_code == 200:
      print("SUCCESS: MLflow experiment created!")
      experiment_result = response.json()
      experiment_id = experiment_result.get('experiment_id')
    else:
      print(f"Experiment error: {response.text}")
      experiment_id = '0'  # Use default

    result = {
        "message": "MLflow integration working!",
        "input_data": input_data,
        "experiment_created": response.status_code == 200
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
