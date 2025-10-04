# AWS Lambda - Autocaris XML Downloader Documentation

## Overview
This AWS Lambda function downloads XML car listing data from Autocaris via HTTP POST request and automatically saves it to an Amazon S3 bucket. Designed for serverless execution, it runs on-demand or on a schedule without maintaining infrastructure.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Configuration](#configuration)
3. [Function Details](#function-details)
4. [AWS Setup](#aws-setup)
5. [Deployment](#deployment)
6. [Scheduling](#scheduling)
7. [Error Handling](#error-handling)
8. [Monitoring](#monitoring)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components
```
Lambda Function
    ↓
HTTP POST → Autocaris API
    ↓
Download XML Response
    ↓
Upload to S3 Bucket
    ↓
Return Success/Failure
```

### AWS Services Used
- **AWS Lambda** - Serverless compute
- **Amazon S3** - Object storage
- **CloudWatch** - Logging and monitoring
- **EventBridge** (optional) - Scheduling

---

## Configuration

### Required Credentials

```python
# Autocaris API credentials
post_data = {
    "name": "",      # API username
    "password": "",  # API password
    "id": ""        # Account/company ID
}
```

**⚠️ Security Note:** Never hardcode credentials. Use AWS Secrets Manager or environment variables.

### S3 Configuration

```python
bucket_name = "autocaris-data"           # S3 bucket name
s3_key = "inzeraty/inzeraty_usti.xml"   # File path in bucket
```

**Bucket Structure:**
```
autocaris-data/
└── inzeraty/
    └── inzeraty_usti.xml
```

### API Endpoint

```python
url = "https://www.autocaris.cz/downloadcontent/cars.php"
```

---

## Function Details

### `lambda_handler(event, context)`
Main Lambda entry point executed by AWS.

**Parameters:**
- `event` (dict): Event data passed to Lambda
- `context` (object): Runtime information

**Returns:**
- `dict`: Status code and message

**Workflow:**

1. **Prepare POST Data**
```python
data_encoded = urllib.parse.urlencode(post_data).encode("utf-8")
```
Converts dictionary to URL-encoded format: `name=value&password=value&id=value`

2. **Create HTTP Request**
```python
req = urllib.request.Request(url, data=data_encoded)
req.add_header("Content-Type", "application/x-www-form-urlencoded")
```

3. **Execute Request**
```python
with urllib.request.urlopen(req) as response:
    xml_data = response.read()
```

4. **Upload to S3**
```python
s3 = boto3.client("s3")
s3.put_object(
    Bucket=bucket_name,
    Key=s3_key,
    Body=xml_data,
    ContentType="application/xml"
)
```

5. **Return Success**
```python
return {
    "statusCode": 200,
    "body": "XML úspěšně uložen do s3://..."
}
```

---

## AWS Setup

### 1. Create S3 Bucket

**Via AWS Console:**
1. Go to S3 console
2. Click "Create bucket"
3. Name: `autocaris-data`
4. Region: Choose your region
5. Block public access: Keep enabled
6. Create bucket

**Via AWS CLI:**
```bash
aws s3 mb s3://autocaris-data --region eu-central-1
```

### 2. Create IAM Role for Lambda

**Required Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::autocaris-data/*"
    }
  ]
}
```

**Trust Relationship:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 3. Create Lambda Function

**Via AWS Console:**
1. Go to Lambda console
2. Click "Create function"
3. Choose "Author from scratch"
4. Function name: `autocaris-xml-downloader`
5. Runtime: Python 3.11
6. Architecture: x86_64
7. Execution role: Use existing role (created above)
8. Create function

**Via AWS CLI:**
```bash
aws lambda create-function \
  --function-name autocaris-xml-downloader \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-s3-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
```

---

## Deployment

### Method 1: AWS Console

1. **Navigate to Lambda function**
2. **Code source section**
3. **Paste the code**
4. **Deploy**

### Method 2: AWS CLI

**Create deployment package:**
```bash
# Create directory
mkdir autocaris-lambda
cd autocaris-lambda

# Create lambda_function.py with your code
nano lambda_function.py

# Zip the file
zip function.zip lambda_function.py

# Upload to Lambda
aws lambda update-function-code \
  --function-name autocaris-xml-downloader \
  --zip-file fileb://function.zip
```

### Method 3: Using Environment Variables

**Improved version with environment variables:**

```python
import boto3
import urllib.parse
import urllib.request
import os

def lambda_handler(event, context):
    # Get credentials from environment variables
    url = os.environ.get('AUTOCARIS_URL', 
        'https://www.autocaris.cz/downloadcontent/cars.php')
    
    post_data = {
        "name": os.environ.get('AUTOCARIS_USER'),
        "password": os.environ.get('AUTOCARIS_PASSWORD'),
        "id": os.environ.get('AUTOCARIS_ID')
    }
    
    bucket_name = os.environ.get('S3_BUCKET', 'autocaris-data')
    s3_key = os.environ.get('S3_KEY', 'inzeraty/inzeraty_usti.xml')
    
    # Rest of the code...
```

**Set environment variables:**
```bash
aws lambda update-function-configuration \
  --function-name autocaris-xml-downloader \
  --environment Variables="{
    AUTOCARIS_USER=your_username,
    AUTOCARIS_PASSWORD=your_password,
    AUTOCARIS_ID=your_id,
    S3_BUCKET=autocaris-data,
    S3_KEY=inzeraty/inzeraty_usti.xml
  }"
```

---

## Scheduling

### Using EventBridge (CloudWatch Events)

**Schedule Expression Examples:**

| Schedule | Expression |
|----------|-----------|
| Every hour | `rate(1 hour)` |
| Every 6 hours | `rate(6 hours)` |
| Daily at 2 AM UTC | `cron(0 2 * * ? *)` |
| Every weekday at 9 AM | `cron(0 9 ? * MON-FRI *)` |
| Twice daily (6 AM, 6 PM) | `cron(0 6,18 * * ? *)` |

**Via AWS Console:**

1. Go to Lambda function
2. Click "Add trigger"
3. Select "EventBridge (CloudWatch Events)"
4. Create new rule
5. Rule name: `autocaris-daily-sync`
6. Schedule expression: `rate(1 day)`
7. Enable trigger
8. Add

**Via AWS CLI:**

```bash
# Create EventBridge rule
aws events put-rule \
  --name autocaris-daily-sync \
  --schedule-expression "rate(1 day)"

# Add Lambda permission
aws lambda add-permission \
  --function-name autocaris-xml-downloader \
  --statement-id autocaris-eventbridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT_ID:rule/autocaris-daily-sync

# Add Lambda as target
aws events put-targets \
  --rule autocaris-daily-sync \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT_ID:function:autocaris-xml-downloader"
```

---

## Error Handling

### Enhanced Version with Error Handling

```python
import boto3
import urllib.parse
import urllib.request
import json
from urllib.error import HTTPError, URLError

def lambda_handler(event, context):
    try:
        # Prepare data
        url = "https://www.autocaris.cz/downloadcontent/cars.php"
        post_data = {
            "name": os.environ.get('AUTOCARIS_USER'),
            "password": os.environ.get('AUTOCARIS_PASSWORD'),
            "id": os.environ.get('AUTOCARIS_ID')
        }
        
        # Validate credentials
        if not all(post_data.values()):
            raise ValueError("Missing required credentials")
        
        # Encode data
        data_encoded = urllib.parse.urlencode(post_data).encode("utf-8")
        
        # Create request
        req = urllib.request.Request(url, data=data_encoded)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("User-Agent", "AWS-Lambda-Autocaris-Downloader/1.0")
        
        # Execute request with timeout
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                raise Exception(f"HTTP Error: {response.status}")
            
            xml_data = response.read()
            
            # Validate XML data
            if not xml_data or len(xml_data) < 100:
                raise ValueError("Received empty or invalid XML data")
        
        # Upload to S3
        s3 = boto3.client("s3")
        bucket_name = os.environ.get('S3_BUCKET', 'autocaris-data')
        s3_key = os.environ.get('S3_KEY', 'inzeraty/inzeraty_usti.xml')
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=xml_data,
            ContentType="application/xml",
            Metadata={
                'source': 'autocaris',
                'timestamp': str(context.aws_request_id)
            }
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Success",
                "bucket": bucket_name,
                "key": s3_key,
                "size": len(xml_data)
            })
        }
        
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return {
            "statusCode": e.code,
            "body": json.dumps({"error": f"HTTP Error: {e.reason}"})
        }
        
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Connection Error: {e.reason}"})
        }
        
    except ValueError as e:
        print(f"Validation Error: {str(e)}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
        
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal error occurred"})
        }
```

---

## Monitoring

### CloudWatch Logs

**Log Group:** `/aws/lambda/autocaris-xml-downloader`

**View logs via AWS CLI:**
```bash
aws logs tail /aws/lambda/autocaris-xml-downloader --follow
```

### CloudWatch Metrics

**Automatic Metrics:**
- Invocations
- Duration
- Errors
- Throttles

**Create Custom Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name autocaris-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=autocaris-xml-downloader
```

### S3 Event Notifications

**Monitor successful uploads:**

```python
# Add to Lambda code
import json

# After successful S3 upload
print(json.dumps({
    'event': 'upload_success',
    'bucket': bucket_name,
    'key': s3_key,
    'size': len(xml_data),
    'timestamp': context.aws_request_id
}))
```

---

## Security

### Best Practices

1. **Use AWS Secrets Manager**
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# In lambda_handler
credentials = get_secret('autocaris-credentials')
post_data = {
    "name": credentials['username'],
    "password": credentials['password'],
    "id": credentials['id']
}
```

2. **S3 Bucket Encryption**
```bash
aws s3api put-bucket-encryption \
  --bucket autocaris-data \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

3. **VPC Configuration (Optional)**
- Place Lambda in private subnet
- Use NAT Gateway for internet access
- Add security groups

4. **Least Privilege IAM**
- Only grant necessary S3 permissions
- Restrict to specific bucket/prefix
- Use resource-based policies

---

## Troubleshooting

### Common Issues

#### 1. "Access Denied" S3 Error

**Cause:** Lambda role lacks S3 permissions

**Solution:**
```bash
aws iam attach-role-policy \
  --role-name lambda-s3-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

#### 2. "Task timed out after 3.00 seconds"

**Cause:** Default timeout too short

**Solution:**
```bash
aws lambda update-function-configuration \
  --function-name autocaris-xml-downloader \
  --timeout 30
```

#### 3. HTTP 403 Forbidden from Autocaris

**Cause:** Invalid credentials or blocked IP

**Solution:**
- Verify credentials
- Contact Autocaris support for IP whitelisting
- Check if API requires specific User-Agent

#### 4. Empty XML Downloaded

**Cause:** Authentication failure or API change

**Solution:**
- Add validation in code
- Log response headers
- Test credentials manually

---

## Testing

### Manual Test

**Via AWS Console:**
1. Go to Lambda function
2. Click "Test"
3. Create test event (empty JSON: `{}`)
4. Click "Test"
5. Check execution results

**Via AWS CLI:**
```bash
aws lambda invoke \
  --function-name autocaris-xml-downloader \
  --payload '{}' \
  response.json

cat response.json
```

### Verify S3 Upload

```bash
# List files
aws s3 ls s3://autocaris-data/inzeraty/

# Download file
aws s3 cp s3://autocaris-data/inzeraty/inzeraty_usti.xml ./

# Check file size
ls -lh inzeraty_usti.xml
```

---

## Cost Estimation

### AWS Lambda Pricing (eu-central-1)

- **Requests:** $0.20 per 1M requests
- **Duration:** $0.0000166667 per GB-second

**Example (Daily execution):**
- 30 executions/month
- 128 MB memory
- 5 seconds duration
- **Cost:** ~$0.01/month

### S3 Pricing

- **Storage:** $0.023 per GB/month
- **PUT requests:** $0.005 per 1,000 requests

**Example:**
- 1 MB file x 30/month
- 30 PUT requests
- **Cost:** ~$0.001/month

**Total:** < $0.02/month

---

## Future Enhancements

### 1. Version Control
```python
from datetime import datetime

# Add timestamp to filename
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
s3_key = f"inzeraty/inzeraty_usti_{timestamp}.xml"
```

### 2. SNS Notifications
```python
import boto3

sns = boto3.client('sns')
sns.publish(
    TopicArn='arn:aws:sns:region:account:autocaris-alerts',
    Subject='Autocaris XML Downloaded',
    Message=f'Successfully downloaded {len(xml_data)} bytes'
)
```

### 3. Data Validation
```python
import xml.etree.ElementTree as ET

# Validate XML structure
try:
    root = ET.fromstring(xml_data)
    car_count = len(root.findall('.//car'))
    print(f"Valid XML with {car_count} cars")
except ET.ParseError as e:
    print(f"Invalid XML: {e}")
    raise
```

---

## License

Proprietary - For use with Autocaris API integration only.

---

## Support

For issues:
1. Check CloudWatch Logs
2. Verify IAM permissions
3. Test API credentials
4. Confirm S3 bucket exists
5. Check network connectivity
