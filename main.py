import boto3
import urllib.parse
import urllib.request

def lambda_handler(event, context):
    # Připrav data
    url = "https://www.autocaris.cz/downloadcontent/cars.php"
    post_data = {
        "name": "",
        "password": "",
        "id": ""
    }
    
    # Zakóduj data pro POST
    data_encoded = urllib.parse.urlencode(post_data).encode("utf-8")
    
    # Připrav požadavek
    req = urllib.request.Request(url, data=data_encoded)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    # Odeslat request
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()

    # Uložit do S3
    s3 = boto3.client("s3")
    bucket_name = "autocaris-data"  # změň na svůj bucket
    s3_key = "inzeraty/inzeraty_usti.xml"

    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=xml_data,
        ContentType="application/xml"
    )

    return {
        "statusCode": 200,
        "body": f"XML úspěšně uložen do s3://{bucket_name}/{s3_key}"
    }
