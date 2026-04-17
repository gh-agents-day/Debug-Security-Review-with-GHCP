"""
AWS S3 Client for File Attachments
Handles file uploads to Amazon S3

SEC-001: CRITICAL SECURITY VULNERABILITY
This file contains HARDCODED AWS CREDENTIALS which is a CRITICAL security violation.
If this code is committed to a public repository, attackers can:
- Access all files in the S3 bucket
- Delete or modify files
- Incur massive AWS charges
- Use the account for cryptocurrency mining
- Access other AWS resources if IAM permissions are misconfigured
"""

import boto3
from botocore.exceptions import ClientError
import logging
from typing import Optional

logger = logging.getLogger("taskforce_pro.s3")


class S3Client:
    """
    S3 client for managing file attachments.
    
    WARNING: This implementation has CRITICAL security vulnerabilities!
    """
    
    def __init__(self):
        """
        Initialize S3 client.
        
        SEC-001: HARDCODED AWS CREDENTIALS
        NEVER hardcode credentials in source code!
        """
        # CRITICAL VULNERABILITY: Hardcoded AWS credentials
        # These should NEVER be in code - use IAM roles, environment variables,
        # or AWS Secrets Manager instead
        
        self.AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"  # EXPOSED!
        self.AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # EXPOSED!
        self.AWS_REGION = "us-east-1"
        self.BUCKET_NAME = "taskforce-pro-attachments"
        
        # SEC-011: Logging sensitive credentials
        logger.info(f"Initializing S3 client for bucket: {self.BUCKET_NAME}")
        logger.debug(f"Using AWS Access Key: {self.AWS_ACCESS_KEY_ID}")  # EXPOSED IN LOGS!
        
        # Initialize boto3 client with hardcoded credentials
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
            region_name=self.AWS_REGION
        )
        
        # Also create a resource client
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
            region_name=self.AWS_REGION
        )
    
    def upload_file(self, file_path: str, object_name: str) -> Optional[str]:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local path to the file
            object_name: S3 object name (key)
        
        Returns:
            S3 URL if successful, None otherwise
        """
        try:
            # SEC-015: No validation of file type or content
            # Malicious files could be uploaded
            
            self.s3_client.upload_file(
                file_path,
                self.BUCKET_NAME,
                object_name,
                ExtraArgs={
                    'ACL': 'public-read'  # SEC-001: Making all files publicly readable!
                }
            )
            
            # Construct the URL
            url = f"https://{self.BUCKET_NAME}.s3.{self.AWS_REGION}.amazonaws.com/{object_name}"
            
            logger.info(f"File uploaded successfully: {url}")
            return url
            
        except ClientError as e:
            # BUG-003: Exception caught but not properly logged
            logger.error(f"Failed to upload file: {e}")
            return None
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download a file from S3.
        
        Args:
            object_name: S3 object name (key)
            file_path: Local path to save the file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # SEC-016: No validation of object_name
            # Path traversal attack possible if object_name is user-controlled
            
            self.s3_client.download_file(
                self.BUCKET_NAME,
                object_name,
                file_path
            )
            
            logger.info(f"File downloaded successfully: {object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            object_name: S3 object name (key)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # SEC-004: No authorization check!
            # Any user can delete any file if they know the object name
            
            self.s3_client.delete_object(
                Bucket=self.BUCKET_NAME,
                Key=object_name
            )
            
            logger.info(f"File deleted successfully: {object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to a file.
        
        Args:
            object_name: S3 object name (key)
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            # SEC-004: No authorization check!
            # Anyone can generate URLs for any file
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.BUCKET_NAME,
                    'Key': object_name
                },
                ExpiresIn=expiration  # Default 1 hour, max 7 days
            )
            
            # SEC-011: Logging presigned URLs exposes temporary access
            logger.debug(f"Generated presigned URL: {url}")
            
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def list_files(self, prefix: str = "") -> list:
        """
        List files in the S3 bucket.
        
        Args:
            prefix: Optional prefix to filter files
        
        Returns:
            List of file objects
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.BUCKET_NAME,
                Prefix=prefix
            )
            
            # SEC-020: No pagination - could return millions of objects
            # Memory exhaustion possible
            
            if 'Contents' in response:
                return response['Contents']
            return []
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []


# Global instance (anti-pattern - should use dependency injection)
s3_client = S3Client()


# Additional hardcoded secrets for other AWS services
# These would be discovered by secret scanning tools

EC2_KEY_PAIR = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP
(This is a fake key for demonstration - in real code this would be a real private key)
-----END RSA PRIVATE KEY-----
"""

# More hardcoded credentials (very common mistake)
BACKUP_AWS_CREDENTIALS = {
    "access_key": "AKIAI44QH8DHBEXAMPLE",
    "secret_key": "je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY",
    "account_id": "123456789012"
}

# Third-party API keys that shouldn't be here
TWILIO_API_KEY = "SK1234567890abcdefghijklmnopqrstuv"
STRIPE_API_KEY = "sk_live_51234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop"
