import json
import boto3
import mlflow
import os

# Initialize the MLflow tracking URI
tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

print(f"Tracking URI: {tracking_uri}")
print(f"Tracking Server ARN: {tracking_server_arn}")


def lambda_handler(event, context):
  # Parse the incoming request
  try:
    body = json.loads(event['body'])
    input_data = body.get('input_data')

    print(f"body: {body}")

    # Log the input data to MLflow

    os.environ['MLFLOW_TRACKING_SERVER_ARN'] = tracking_server_arn
    mlflow.set_tracking_uri(tracking_uri)
    print("after setting tracking URI")
    print(f"MLflow tracking URI set to: {mlflow.get_tracking_uri()}")

    with mlflow.start_run():
      print("Starting MLflow run")
      mlflow.log_param("input_data", input_data)
    # Parse the response from SageMaker
    # result = json.loads(response['Body'].read().decode())
    print("after logging input data")
    result = {
        "message": "This is a mock response for input"
    }

    # # Log the result to MLflow
    # mlflow.log_metric("inference_result", result)

    # Return the result as a JSON response
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
