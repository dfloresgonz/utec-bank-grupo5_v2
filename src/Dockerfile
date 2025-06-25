FROM public.ecr.aws/lambda/python:3.9

# Copy the function code
COPY app/lambda_function.py ${LAMBDA_TASK_ROOT}

# Command to run the Lambda function
CMD ["lambda_function.lambda_handler"]