import json
import boto3
import mlflow
import os
from mlflow.tracking import MlflowClient
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
  try:
    # Obtener variables de entorno
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    tracking_server_arn = os.environ.get("MLFLOW_TRACKING_SERVER_ARN")

    logger.info(f"Tracking URI: {tracking_uri}")
    logger.info(f"Tracking Server ARN: {tracking_server_arn}")

    # Configurar sesión AWS con credenciales
    session = boto3.Session()
    credentials = session.get_credentials()

    # Configurar MLflow con headers de autenticación AWS
    mlflow.set_tracking_uri(tracking_uri)

    # Add AWS SigV4 authentication
    from requests_auth_aws_sigv4 import AWSSigV4
    aws_auth = AWSSigV4(
        'sagemaker',
        region_name=session.region_name,
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token
    )

    # Set the auth for MLflow
    mlflow.tracking.set_tracking_uri(tracking_uri)
    mlflow.tracking._tracking_service.utils._get_default_host_creds = lambda: mlflow.tracking.request_header.construct_basic_auth(
        aws_auth
    )

    # Parse the incoming request
    body = json.loads(event['body'])
    input_data = body.get('input_data')

    # Rest of your code...
