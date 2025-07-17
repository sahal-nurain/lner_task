# 🚆 LNER Task — Kinesis + DynamoDB + Lambda (LocalStack)

This project simulates a train delay data processing pipeline using **AWS Kinesis**, **AWS Lambda**, and **DynamoDB**, all powered locally with **LocalStack** for development and testing.

## 📆 Project Structure

```
lner-task/
├── processor/               # Consumer Lambda source (etl.py)
├── service/                 # Producer Lambda source (app.py, data file)
├── terraform/               # Terraform IaC configuration
├── consumer.zip             # Zipped consumer Lambda code (auto-generated)
├── producer.zip             # Zipped producer Lambda code (auto-generated)
└── README.md                # This file
```

---

## 🧰 Components

### ✅ Producer Lambda
- Reads data from a JSON file (`delays_data_DE_technical_interview2.json`)
- Sends events to a Kinesis stream (`train-stream`)

### ✅ Kinesis Stream
- Acts as a transport layer for delay data events

### ✅ Consumer Lambda
- Triggered by Kinesis
- Parses and stores records in a DynamoDB table (`pipeline_status`)

### ✅ DynamoDB
- Stores parsed train delay records keyed by `record_id`

---

## 🐳 Running Locally with LocalStack

LocalStack emulates AWS services on your machine. You can run all of this **without real AWS credentials**.

Start LocalStack (if you’re using Docker):

```bash
docker-compose up
```

---

## 📁 Packaging the Lambdas

To prepare your Lambdas for Terraform deployment:

```bash
# Create package directories
mkdir -p processor_package
mkdir -p producer_package

# Package the processor (consumer) Lambda
cd processor_package
pip install sqlalchemy pg8000 --target .
cp ../processor/etl.py .
zip -r ../consumer.zip .
cd ..

# Package the producer Lambda
cd producer_package
cp ../service/app.py .
cp ../service/delays_data_DE_technical_interview2.json .
zip -r ../producer.zip .
cd ..

# Copy zips into terraform dir
cp consumer.zip producer.zip terraform/
cd terraform
```

---

## 🌍 Terraform Deployment

Deploy the infrastructure locally with:

```bash
cd terraform
terraform init
terraform apply
```

Make sure your `provider` block in Terraform uses LocalStack endpoints and dummy credentials (as already configured in `main.tf`).

---

## 🦖 Testing

You can trigger the **producer Lambda** manually to inject data:

```bash
awslocal lambda invoke \
  --function-name producer-lambda \
  --payload '{}' \
  output.json
```

To inspect the data stored in DynamoDB:

```bash
awslocal dynamodb scan \
  --table-name pipeline_status \
  --output table
```

---

## 📅 Notes

- This setup uses **Terraform** to provision all resources
- Local development is enabled via **LocalStack**
- Be sure to **repackage zips** whenever you change Lambda source files

