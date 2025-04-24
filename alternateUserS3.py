import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def rotate_s3_secret(service_client, arn, token):
    """
    Rotates an S3 secret stored in AWS Secrets Manager.

    This function generates a new access key for an IAM user, updates the secret in Secrets Manager,
    and deactivates the old access key.

    Args:
        service_client (boto3.client): The Secrets Manager service client.
        arn (str): The ARN of the secret to rotate.
        token (str): The ClientRequestToken associated with the secret version.

    Raises:
        ValueError: If the secret is not properly configured for rotation.
    """
    # Retrieve the current secret
    current_secret = get_secret_dict(service_client, arn, "AWSCURRENT")

    # Ensure the secret contains the required keys
    required_keys = ["aws_access_key_id", "aws_secret_access_key", "iam_user"]
    for key in required_keys:
        if key not in current_secret:
            raise ValueError(f"Missing required key '{key}' in secret.")

    iam_user = current_secret["iam_user"]

    # Create a new access key for the IAM user
    iam_client = boto3.client("iam")
    new_access_key = iam_client.create_access_key(UserName=iam_user)
    new_secret = {
        "aws_access_key_id": new_access_key["AccessKey"]["AccessKeyId"],
        "aws_secret_access_key": new_access_key["AccessKey"]["SecretAccessKey"],
        "iam_user": iam_user,
    }

    # Store the new secret in Secrets Manager with the AWSPENDING stage
    service_client.put_secret_value(
        SecretId=arn,
        ClientRequestToken=token,
        SecretString=json.dumps(new_secret),
        VersionStages=["AWSPENDING"],
    )
    logger.info(f"rotate_s3_secret: Successfully created new access key for IAM user {iam_user}.")

    # Deactivate the old access key
    old_access_key_id = current_secret["aws_access_key_id"]
    iam_client.update_access_key(
        UserName=iam_user,
        AccessKeyId=old_access_key_id,
        Status="Inactive",
    )
    logger.info(f"rotate_s3_secret: Deactivated old access key for IAM user {iam_user}.")

    # Optionally, delete the old access key
    # iam_client.delete_access_key(UserName=iam_user, AccessKeyId=old_access_key_id)


def get_secret_dict(service_client, arn, stage):
    """
    Retrieves the secret dictionary for the specified ARN and stage.

    Args:
        service_client (boto3.client): The Secrets Manager service client.
        arn (str): The ARN of the secret.
        stage (str): The stage of the secret (e.g., AWSCURRENT, AWSPENDING).

    Returns:
        dict: The secret dictionary.

    Raises:
        ValueError: If the secret is not valid JSON.
    """
    secret_value = service_client.get_secret_value(SecretId=arn, VersionStage=stage)
    secret_string = secret_value["SecretString"]
    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        raise ValueError("Secret is not valid JSON.")