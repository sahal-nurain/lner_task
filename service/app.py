import json
import boto3
import os
import unittest
from pathlib import Path

endpoint_url = os.environ.get("AWS_ENDPOINT_URL", "http://host.docker.internal:4566")

kinesis = boto3.client('kinesis', endpoint_url=endpoint_url)

DATA_FILE = "delays_data_DE_technical_interview2.json"

def has_incident_field(record):
    """
    Check if a record has the is_incident field.
    
    Args:
        record (dict): Record to check
        
    Returns:
        bool: True if field exists, False otherwise
    """
    return "is_incident" in record

def has_timestamp_field(record):
    """
    Check if a record has the timestamp field.
    
    Args:
        record (dict): Record to check
        
    Returns:
        bool: True if field exists, False otherwise
    """
    return "timestamp" in record

def notify_missing_field(record_id, field_name):
    """
    Log a message about missing field and in a real environment, would notify via SNS.
    """
    print(f"CRITICAL: Record {record_id} missing required '{field_name}' field")
    # In a real production environment, we would use SNS to notify required parties:
    # sns_client = boto3.client('sns')
    # sns_client.publish(
    #     TopicArn='arn:aws:sns:region:account-id:incident-notification',
    #     Message=f"Missing '{field_name}' field in record {record_id}",
    #     Subject='Data Quality Alert: Missing Critical Field'
    # )

def handler(event, context):
    """
    Lambda handler function that processes records and sends them to Kinesis.
    """
    records = json.loads(Path(DATA_FILE).read_text())
    print(f"Loaded {len(records)} records from {DATA_FILE}")
    
    success_count = 0
    missing_incident_field = 0
    missing_timestamp_field = 0
    
    for record in records:
        record_id = record.get("Unnamed: 0", "unknown")
        valid_record = True
        
        # Check for required fields
        if not has_incident_field(record):
            notify_missing_field(record_id, "is_incident")
            valid_record = False
            missing_incident_field += 1
            
        if not has_timestamp_field(record):
            notify_missing_field(record_id, "timestamp")
            valid_record = False
            missing_timestamp_field += 1
        
        # Only send valid records to Kinesis
        if valid_record:
            try:
                kinesis.put_record(
                    StreamName="train-stream",
                    Data=json.dumps(record),
                    PartitionKey=str(record_id)
                )
                success_count += 1
            except Exception as e:
                print(f"Error sending record {record_id}: {str(e)}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "total_records": len(records),
            "success_count": success_count,
            "missing_incident_field": missing_incident_field,
            "missing_timestamp_field": missing_timestamp_field
        })
    }


# Unit Tests
class TestRecordValidation(unittest.TestCase):
    """
    Unit tests for record validation functions
    """
    def test_has_incident_field(self):
        # Test with field present
        record_with_field = {"is_incident": True, "Unnamed: 0": 1}
        self.assertTrue(has_incident_field(record_with_field))
        
        # Test with field missing
        record_without_field = {"Unnamed: 0": 2}
        self.assertFalse(has_incident_field(record_without_field))
    
    def test_has_timestamp_field(self):
        # Test with field present
        record_with_field = {"timestamp": "2023-01-01", "Unnamed: 0": 1}
        self.assertTrue(has_timestamp_field(record_with_field))
        
        # Test with field missing
        record_without_field = {"Unnamed: 0": 2}
        self.assertFalse(has_timestamp_field(record_without_field))


if __name__ == "__main__":
    # Run the unit tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # After tests run, execute the main handler
    print("\n--- Running main application ---")
    result = handler(None, None)
    print(f"Execution completed with status code: {result['statusCode']}")
    print(f"Results: {result['body']}")
