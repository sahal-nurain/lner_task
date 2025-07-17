import json
import boto3
import base64
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Table, MetaData, DateTime, Boolean
from sqlalchemy.dialects.postgresql import insert as pg_insert

endpoint_url = os.environ.get("AWS_ENDPOINT_URL", "http://host.docker.internal:4566")

dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
table = dynamodb.Table("pipeline_status")


def transform_record(record):
    # Rename Unnamed: 0 to record_id
    record["record_id"] = str(record.pop("Unnamed: 0", "unknown"))

    # Construct timestamp
    try:
        year = int(record.get("year", 2025))
        month = int(record.get("month", 1))
        day = int(record.get("day", 1))
        hour = int(record.get("location_hour", 0))
        # Store as a datetime object, not as a string
        record["timestamp"] = datetime(year, month, day, hour)
    except Exception as e:
        record["timestamp"] = None

    # Normalize dwell_time
    try:
        record["dwell_time"] = round(float(record.get("dwell_time", 0)))
    except:
        record["dwell_time"] = 0

    # Normalize location
    if "location" in record:
        record["location"] = record["location"].strip().upper()
        
    # Map is_incident field to incident (keeping it as boolean)
    if "is_incident" in record:
        record["incident"] = bool(record["is_incident"])
        
    # Convert month names to numbers if they are strings
    if "month" in record and isinstance(record["month"], str):
        month_mapping = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        record["month"] = month_mapping.get(record["month"], 1)  # Default to 1 if not found
        
    # Convert day names to numbers if they are strings
    if "day" in record and isinstance(record["day"], str):
        day_mapping = {
            "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4,
            "Friday": 5, "Saturday": 6, "Sunday": 7
        }
        record["day"] = day_mapping.get(record["day"], 1)  # Default to 1 if not found

    return record


def insert_into_postgres(record, engine):
    # Define the delays table structure
    metadata = MetaData()
    delays = Table(
        'delays', metadata,
        Column('record_id', String, primary_key=True),
        Column('timestamp', DateTime),
        Column('flight_id', String),
        Column('location', String),
        Column('location_hour', Integer),
        Column('location_part_of_day', String),
        Column('delay_category', String),
        Column('dwell_time', Integer),
        Column('incident', Boolean),
        Column('year', Integer),
        Column('month', Integer),
        Column('day', Integer)
    )
    
    # Create an insert statement with ON CONFLICT DO NOTHING
    insert_stmt = pg_insert(delays).values(
        record_id=record["record_id"],
        timestamp=record.get("timestamp"),
        flight_id=record.get("flight_id"),
        location=record.get("location"),
        location_hour=record.get("location_hour"),
        location_part_of_day=record.get("location_part_of_day"),
        delay_category=record.get("delay_category"),
        dwell_time=record.get("dwell_time"),
        incident=record.get("incident"),
        year=record.get("year"),
        month=record.get("month"),
        day=record.get("day")
    ).on_conflict_do_nothing()
    
    # Execute the insert
    with engine.begin() as conn:
        conn.execute(insert_stmt)




def record_status(record_id, status, error=None):
    item = {
        "record_id": record_id,
        "status": status
    }
    if error:
        item["error"] = error
    table.put_item(Item=item)

def handler(event, context):
    success_count, failure_count = 0, 0

    for record in event.get("Records", []):
        try:
            payload = record["kinesis"]["data"]
            
            decoded = json.loads(base64.b64decode(payload).decode("utf-8"))

            transformed = transform_record(decoded)
            
            print(f"[INFO] Transformed: {transformed}")
            
            # Create SQLAlchemy engine
            engine = create_engine(
                "postgresql+pg8000://postgres:postgres@host.docker.internal:5432/train_data"
            )
            
            insert_into_postgres(transformed, engine)


            record_status(transformed["record_id"], "success")
            success_count += 1

        except Exception as e:
            print(f"[ERROR] Failed to process record: {e}")
            record_id = decoded.get("Unnamed: 0", "unknown") if "decoded" in locals() else "unknown"
            record_status(str(record_id), "error", str(e))
            failure_count += 1
        
        finally:
            # SQLAlchemy manages connection closing automatically
            pass

    return {
        "statusCode": 200,
        "body": json.dumps({
            "success": success_count,
            "failed": failure_count
        })
    }
