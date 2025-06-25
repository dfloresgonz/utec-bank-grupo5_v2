FROM public.ecr.aws/lambda/python:3.9

# Upgrade pip first
RUN pip install --upgrade pip

# Install Python dependencies with verbose output for debugging
RUN pip install --no-cache-dir --verbose \
    mlflow==2.13.2 \
    sagemaker-mlflow==0.1.0 \
    xgboost==2.1.4 \
    boto3 \
    numpy \
    pandas

# Verify installations
RUN python -c "import mlflow; print(f'MLflow version: {mlflow.__version__}')" && \
    python -c "import boto3; print('boto3 imported successfully')" && \
    python -c "import pandas; print('pandas imported successfully')" && \
    python -c "import numpy; print('numpy imported successfully')"

# Copy the function code
COPY app/lambda_function.py ${LAMBDA_TASK_ROOT}/

# Command to run the Lambda function
CMD ["lambda_function.lambda_handler"]