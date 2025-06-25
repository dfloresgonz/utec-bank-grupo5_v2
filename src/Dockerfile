FROM public.ecr.aws/lambda/python:3.9

RUN pip install --no-cache-dir mlflow==2.13.2 sagemaker-mlflow==0.1.0 xgboost==2.1.4 boto3 numpy pandas 

# Copy the function code
COPY app/lambda_function.py ${LAMBDA_TASK_ROOT}

# Command to run the Lambda function
CMD ["lambda_function.lambda_handler"]