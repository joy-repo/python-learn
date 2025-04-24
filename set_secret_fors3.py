import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def set_secret(service_client, arn, token):
    """
    Set the pending secret for S3 in AWS Secrets Manager.

    This function updates the S3 credentials in Secrets Manager by validating the pending secret
    and ensuring it is correctly configured.

    Args:
        service_client (boto3.client): The Secrets Manager service client.
        arn (str): The ARN of the secret to rotate.
        token (str): The ClientRequestToken associated with the secret version.

    Raises:
        ValueError: If the secret is not properly configured for rotation.
    """
    # Retrieve the current and pending secrets
    current_secret = get_secret_dict(service_client, arn, "AWSCURRENT")
    pending_secret = get_secret_dict(service_client, arn, "AWSPENDING", token)

    # Ensure the secret contains the required keys
    required_keys = ["aws_access_key_id", "aws_secret_access_key"]
    for key in required_keys:
        if key not in pending_secret:
            raise ValueError(f"Missing required key '{key}' in pending secret.")

    # Validate the pending secret by attempting to use it
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=pending_secret["aws_access_key_id"],
        aws_secret_access_key=pending_secret["aws_secret_access_key"],
    )

    try:
        # Perform a simple operation to validate the credentials
        s3_client.list_buckets()
        logger.info(f"set_secret: Successfully validated pending secret for ARN {arn}.")
    except Exception as e:
        logger.error(f"set_secret: Failed to validate pending secret for ARN {arn}. Error: {e}")
        raise ValueError(f"Failed to validate pending secret for ARN {arn}. Error: {e}")


def get_secret_dict(service_client, arn, stage, token=None):
    """
    Retrieves the secret dictionary for the specified ARN and stage.

    Args:
        service_client (boto3.client): The Secrets Manager service client.
        arn (str): The ARN of the secret.
        stage (str): The stage of the secret (e.g., AWSCURRENT, AWSPENDING).
        token (str): The ClientRequestToken associated with the secret version (optional).

    Returns:
        dict: The secret dictionary.

    Raises:
        ValueError: If the secret is not valid JSON.
    """
    if token:
        secret_value = service_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage=stage)
    else:
        secret_value = service_client.get_secret_value(SecretId=arn, VersionStage=stage)

    secret_string = secret_value["SecretString"]
    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        raise ValueError("Secret is not valid JSON.")