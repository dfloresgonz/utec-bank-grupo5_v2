import json
import boto3
import os


def lambda_handler(event, context):
  try:
    tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

    # Información detallada del servidor
    sagemaker_client = boto3.client('sagemaker')
    server_info = sagemaker_client.describe_mlflow_tracking_server(
        TrackingServerName=tracking_server_arn.split('/')[-1]
    )

    print(f"Server details:")
    print(f"- Status: {server_info.get('TrackingServerStatus')}")
    print(f"- URL: {server_info.get('TrackingServerUrl')}")
    print(f"- Size: {server_info.get('TrackingServerSize')}")
    print(f"- Artifact Store: {server_info.get('ArtifactStoreUri')}")
    print(f"- Role ARN: {server_info.get('RoleArn')}")
    print(f"- Creation Time: {server_info.get('CreationTime')}")
    print(f"- Last Modified: {server_info.get('LastModifiedTime')}")

    # Verificar permisos del bucket S3
    s3_client = boto3.client('s3')
    bucket_name = "s3-mlflow-artifacts-mlflow-tracking-server-grupo5-01"

    try:
      bucket_location = s3_client.get_bucket_location(Bucket=bucket_name)
      print(f"Bucket location: {bucket_location}")

      # Test write access
      s3_client.put_object(
          Bucket=bucket_name,
          Key='test/lambda-test.txt',
          Body=b'test from lambda'
      )
      print("S3 write test: SUCCESS")

    except Exception as s3_error:
      print(f"S3 access error: {s3_error}")

    body = json.loads(event['body'])
    input_data = body.get('input_data')

    result = {
        "message": "Diagnostic completed",
        "input_data": input_data,
        "server_status": server_info.get('TrackingServerStatus'),
        "server_url": server_info.get('TrackingServerUrl')
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
