provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true

  endpoints {
    lambda    = "http://localhost:4566"
    kinesis   = "http://localhost:4566"
    dynamodb  = "http://localhost:4566"
    iam       = "http://localhost:4566"
    s3        = "http://localhost:4566"
  }
}

# Kinesis stream
resource "aws_kinesis_stream" "train_stream" {
  name        = "train-stream"
  shard_count = 1
}

# DynamoDB table
resource "aws_dynamodb_table" "pipeline_status" {
  name         = "pipeline_status"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "record_id"

  attribute {
    name = "record_id"
    type = "S"
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Producer Lambda: sends JSON data to Kinesis
resource "aws_lambda_function" "producer_lambda" {
  function_name = "producer-lambda"
  handler       = "app.handler"
  runtime       = "python3.9"
  filename      = "producer.zip"
  role          = aws_iam_role.lambda_exec_role.arn
  source_code_hash = filebase64sha256("${path.module}/producer.zip")

  environment {
    variables = {
      STREAM_NAME = aws_kinesis_stream.train_stream.name
      AWS_ENDPOINT_URL = "http://host.docker.internal:4566"
    }
  }
}

# Consumer Lambda: reads from Kinesis and updates DynamoDB
resource "aws_lambda_function" "consumer_lambda" {
  function_name = "consumer-lambda"
  handler       = "etl.handler"
  runtime       = "python3.9"
  filename      = "consumer.zip"
  role          = aws_iam_role.lambda_exec_role.arn
  source_code_hash = filebase64sha256("consumer.zip")

  environment {
    variables = {
      DYNAMO_TABLE = aws_dynamodb_table.pipeline_status.name
      AWS_ENDPOINT_URL = "http://host.docker.internal:4566"
    }
  }
}


# Link: Kinesis → Consumer Lambda
resource "aws_lambda_event_source_mapping" "kinesis_to_consumer" {
  event_source_arn  = aws_kinesis_stream.train_stream.arn
  function_name     = aws_lambda_function.consumer_lambda.arn
  starting_position = "LATEST"
  batch_size        = 1
}

