import json
import boto3
import os
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import time


def lambda_handler(event, context):
  try:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

    print(f"=== MLFLOW DEBUG SESSION ===")
    print(f"Tracking URI: {tracking_uri}")
    print(f"Tracking Server ARN: {tracking_server_arn}")
    print(f"AWS Region: {boto3.Session().region_name}")

    # 1. Verificar estado detallado del tracking server
    sagemaker_client = boto3.client('sagemaker')
    server_info = sagemaker_client.describe_mlflow_tracking_server(
        TrackingServerName=tracking_server_arn.split('/')[-1]
    )

    print(f"\n=== TRACKING SERVER STATUS ===")
    print(f"Status: {server_info.get('TrackingServerStatus')}")
    print(f"Size: {server_info.get('TrackingServerSize')}")
    print(f"Creation Time: {server_info.get('CreationTime')}")
    print(f"Last Modified: {server_info.get('LastModifiedTime')}")
    print(f"Role ARN: {server_info.get('RoleArn')}")
    print(f"Artifact Store: {server_info.get('ArtifactStoreUri')}")

    # 2. Verificar conectividad básica
    print(f"\n=== CONNECTIVITY TEST ===")
    try:
      response = requests.get(f"{tracking_uri}/health", timeout=15)
      print(f"Health endpoint: {response.status_code}")
      print(f"Health response: {response.text[:200]}")
    except Exception as health_error:
      print(f"Health check failed: {health_error}")

    # 3. Test básico sin autenticación
    try:
      response = requests.get(
          f"{tracking_uri}/api/2.0/mlflow/experiments/list", timeout=15)
      print(f"Basic API test (no auth): {response.status_code}")
      print(f"Basic API response: {response.text[:200]}")
    except Exception as basic_error:
      print(f"Basic API test failed: {basic_error}")

    # 4. Verificar permisos S3 específicos
    print(f"\n=== S3 PERMISSIONS TEST ===")
    s3_client = boto3.client('s3')
    bucket_name = "s3-mlflow-artifacts-mlflow-tracking-server-grupo5-01"

    # Test diferentes operaciones S3
    s3_tests = [
        ("list_bucket", lambda: s3_client.list_objects_v2(
            Bucket=bucket_name, MaxKeys=1)),
        ("get_bucket_location", lambda: s3_client.get_bucket_location(Bucket=bucket_name)),
        ("put_object", lambda: s3_client.put_object(
            Bucket=bucket_name, Key='test/lambda-debug.txt', Body=b'debug test')),
        ("get_object", lambda: s3_client.get_object(
            Bucket=bucket_name, Key='test/lambda-debug.txt')),
    ]

    for test_name, test_func in s3_tests:
      try:
        result = test_func()
        print(f"S3 {test_name}: SUCCESS")
      except Exception as s3_error:
        print(f"S3 {test_name}: FAILED - {s3_error}")

    # 5. Test con autenticación AWS correcta
    print(f"\n=== AUTHENTICATED API TEST ===")
    session = boto3.Session()
    credentials = session.get_credentials()

    def make_authenticated_request(endpoint, method='GET', data=None):
      url = f"{tracking_uri}/api/2.0/mlflow/{endpoint}"

      # Preparar request con todos los headers posibles
      request = AWSRequest(method=method, url=url, data=data)

      # Headers específicos para SageMaker MLflow
      request.headers['X-Amz-Tracking-Server-Arn'] = tracking_server_arn
      request.headers['X-Amz-Target'] = 'SageMaker.MLflow'
      request.headers['User-Agent'] = 'aws-cli/2.0 Python/3.9 lambda'

      if data:
        request.headers['Content-Type'] = 'application/json'

      # Firmar con SigV4
      SigV4Auth(credentials, 'sagemaker',
                session.region_name).add_auth(request)

      print(f"Request URL: {url}")
      print(f"Request headers: {dict(request.headers)}")

      response = requests.request(
          method=method,
          url=url,
          headers=dict(request.headers),
          data=data,
          timeout=30
      )
      return response

    # Test diferentes endpoints
    api_tests = [
        ("experiments/list", "GET", None),
        ("experiments/get?experiment_id=0", "GET", None),  # Default experiment
    ]

    for endpoint, method, data in api_tests:
      try:
        response = make_authenticated_request(endpoint, method, data)
        print(f"API {endpoint}: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        print(f"Response headers: {dict(response.headers)}")
      except Exception as api_error:
        print(f"API {endpoint} failed: {api_error}")

    # 6. Test creación con configuración mínima
    print(f"\n=== MINIMAL EXPERIMENT CREATION ===")
    minimal_experiment = {
        "name": f"test-{int(time.time())}"
    }

    try:
      response = make_authenticated_request(
          'experiments/create',
          'POST',
          json.dumps(minimal_experiment)
      )
      print(f"Minimal experiment creation: {response.status_code}")
      print(f"Response: {response.text}")
    except Exception as minimal_error:
      print(f"Minimal experiment creation failed: {minimal_error}")

    # 7. Verificar CloudWatch logs del tracking server
    print(f"\n=== CLOUDWATCH LOGS CHECK ===")
    try:
      logs_client = boto3.client('logs')
      log_groups = logs_client.describe_log_groups(
          logGroupNamePrefix='/aws/sagemaker/MLflowTrackingServer'
      )
      print(
          f"Available log groups: {[lg['logGroupName'] for lg in log_groups['logGroups']]}")

      # Intentar obtener logs recientes
      if log_groups['logGroups']:
        log_group_name = log_groups['logGroups'][0]['logGroupName']
        streams = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )

        if streams['logStreams']:
          stream_name = streams['logStreams'][0]['logStreamName']
          events = logs_client.get_log_events(
              logGroupName=log_group_name,
              logStreamName=stream_name,
              limit=10,
              startFromHead=False
          )

          print(f"Recent log events:")
          for event in events['events'][-3:]:
            print(f"  {event['timestamp']}: {event['message'][:200]}")
    except Exception as logs_error:
      print(f"CloudWatch logs check failed: {logs_error}")

    body = json.loads(event['body'])
    input_data = body.get('input_data')

    result = {
        "message": "Debug session completed",
        "input_data": input_data,
        "tracking_server_status": server_info.get('TrackingServerStatus'),
        "debugging_info": "Check CloudWatch logs for detailed analysis"
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'result': result})
    }

  except Exception as e:
    print(f"Debug session error: {str(e)}")
    import traceback
    print(f"Full traceback: {traceback.format_exc()}")
    return {
        'statusCode': 500,
        'body': json.dumps({'error': str(e)})
    }
