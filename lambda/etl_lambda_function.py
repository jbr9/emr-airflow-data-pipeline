import boto3
import http.client
import base64
import ast
import json

# Replace with your actual MWAA environment name
mwaa_env_name = '<YOUR_MWAA_ENVIRONMENT_NAME>'

# Replace with your actual DAG name
dag_name = '<YOUR_DAG_NAME>'

# Replace with the MWAA CLI command to trigger the DAG
mwaa_cli_command = 'dags trigger'

client = boto3.client('mwaa')

def lambda_handler(event, context):
    try:

        # Step 1: Parse the event
        detail = event.get("detail", {})
        bucket = detail.get("bucket", {}).get("name")
        key = detail.get("object", {}).get("key")

        if not bucket or not key:
            print("❌ Missing bucket/key in event")
            return {
                "statusCode": 400,
                "body": json.dumps("Missing bucket or key in event")
            }

        # Step 1.5: Validate exact file name
        if key != "<YOUR_EXPECTED_S3_KEY_PATH>":
            print(f"⛔️ Ignored event: key '{key}' does not match '<YOUR_EXPECTED_S3_KEY_PATH>'")
            return {
                "statusCode": 200,
                "message": f"Ignored: Not the target file. Received key: {key}"
            }

        print(f"✅ S3 event parsed: bucket={bucket}, key={key}")

        # Step 3: Get the MWAA CLI token
        mwaa_cli_token = client.create_cli_token(Name=mwaa_env_name)
        print("✅ MWAA CLI token retrieved")
        print(f"mwaa_cli_token['CliToken']={mwaa_cli_token['CliToken']}")

        # Step 4: Setup HTTPS connection to MWAA Webserver
        conn = http.client.HTTPSConnection(mwaa_cli_token['WebServerHostname'])
        payload = f"{mwaa_cli_command} {dag_name}"
        headers = {
            'Authorization': f"Bearer {mwaa_cli_token['CliToken']}",
            'Content-Type': 'text/plain'
        }
        print("✅ HTTPS connection to MWAA Webserver established")

        # Step 5: Send CLI command to trigger DAG
        conn.request("POST", "/aws_mwaa/cli", payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(f"✅ DAG '{dag_name}' trigger sent successfully")

        # Step 6: Parse and log CLI response
        dict_str = data.decode("UTF-8")
        mydata = ast.literal_eval(dict_str)
        stdout = base64.b64decode(mydata.get('stdout', '')).decode("utf-8")
        stderr = base64.b64decode(mydata.get('stderr', '')).decode("utf-8")

        print("STDOUT:", stdout)
        print("STDERR:", stderr)

        # Step 7: Return minimal response to avoid timeouts
        return {
            "statusCode": res.status,
            "message": f"DAG '{dag_name}' trigger sent successfully"
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "error": str(e)
        }
