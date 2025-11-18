"""
AWS helpers for S3 and DynamoDB operations.
"""

import os
import json
import boto3
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class S3Helper:
    """S3 operations."""
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """Upload file to S3. Returns True if successful."""
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            logger.info(f"Uploaded {local_path} → s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def get_object_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get S3 object metadata (size, etag, etc.)."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'size_bytes': response['ContentLength'],
                'etag': response['ETag'],
                'last_modified': response['LastModified'].isoformat(),
                'content_type': response.get('ContentType', 'application/octet-stream')
            }
        except Exception as e:
            logger.error(f"Failed to get S3 metadata: {e}")
            return None


class DynamoDBHelper:
    """DynamoDB operations."""
    
    def __init__(self, table_name: str, region: str = 'us-east-1'):
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def put_item(self, item: Dict[str, Any]) -> bool:
        """Insert or update item in DynamoDB."""
        try:
            self.table.put_item(Item=item)
            logger.info(f"Written to DynamoDB: {item.get('test_id', item.get('id', 'unknown'))}")
            return True
        except Exception as e:
            logger.error(f"DynamoDB put_item failed: {e}")
            return False
    
    def get_item(self, key: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB."""
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except Exception as e:
            logger.error(f"DynamoDB get_item failed: {e}")
            return None
    
    def query_by_section(self, section: str) -> list:
        """Query items by section (if table has section GSI)."""
        try:
            response = self.table.query(
                IndexName='section-created_at-index',
                KeyConditionExpression='section = :section',
                ExpressionAttributeValues={':section': section}
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"DynamoDB query failed: {e}")
            return []


class IngestionHelper:
    """Orchestrate ingestion: validate, upload, store metadata."""
    
    def __init__(self, s3_bucket: str, dynamodb_table: str, region: str = 'us-east-1', dry_run: bool = False):
        self.s3 = S3Helper(s3_bucket, region) if not dry_run else None
        self.dynamodb = DynamoDBHelper(dynamodb_table, region) if not dry_run else None
        self.dry_run = dry_run
        self.region = region
    
    def ingest_listening_test(self, material: Dict[str, Any], audio_local_path: str) -> Dict[str, Any]:
        """
        Ingest a listening test: upload audio, write metadata to DynamoDB.
        Returns metadata dict with S3 keys.
        """
        test_id = material['test_id']
        s3_audio_key = f"exams/listening/{test_id}/audio/{os.path.basename(audio_local_path)}"
        
        if not self.dry_run:
            # Upload audio to S3
            if not self.s3.upload_file(audio_local_path, s3_audio_key):
                raise Exception(f"Failed to upload audio for test {test_id}")
            
            # Get audio metadata
            s3_meta = self.s3.get_object_metadata(s3_audio_key)
            if not s3_meta:
                raise Exception(f"Failed to get S3 metadata for {s3_audio_key}")
        else:
            logger.info(f"[DRY RUN] Would upload {audio_local_path} → {s3_audio_key}")
            s3_meta = {'size_bytes': 0}
        
        # Prepare metadata for DynamoDB
        metadata = {
            'test_id': test_id,
            'section': 'listening',
            'title': material.get('title', ''),
            'description': material.get('description', ''),
            'audio_s3_key': s3_audio_key,
            'audio_duration_seconds': material['audio'].get('duration_seconds', 0),
            'audio_size_bytes': s3_meta.get('size_bytes', 0),
            'transcript': material['transcript']['full_text'],
            'questions_count': len(material.get('questions', [])),
            'total_points': material.get('total_points', 40),
            'source': material['source'],
            'created_at': material.get('created_at', datetime.utcnow().isoformat()),
            'ingested_at': datetime.utcnow().isoformat(),
            'content': material  # Store full material as backup
        }
        
        if not self.dry_run:
            if not self.dynamodb.put_item(metadata):
                raise Exception(f"Failed to write metadata to DynamoDB for test {test_id}")
        else:
            logger.info(f"[DRY RUN] Would write metadata to DynamoDB: {test_id}")
        
        return metadata
    
    def ingest_reading_test(self, material: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a reading test: store metadata only (no assets)."""
        test_id = material['test_id']
        
        # Store passages + questions
        passages_text = '\n---\n'.join(p.get('text', '') for p in material.get('passages', []))
        
        metadata = {
            'test_id': test_id,
            'section': 'reading',
            'title': material.get('title', ''),
            'description': material.get('description', ''),
            'passages_count': len(material.get('passages', [])),
            'questions_count': len(material.get('questions', [])),
            'total_points': material.get('total_points', 40),
            'source': material['source'],
            'created_at': material.get('created_at', datetime.utcnow().isoformat()),
            'ingested_at': datetime.utcnow().isoformat(),
            'content': material
        }
        
        if not self.dry_run:
            if not self.dynamodb.put_item(metadata):
                raise Exception(f"Failed to write metadata to DynamoDB for test {test_id}")
        else:
            logger.info(f"[DRY RUN] Would write metadata to DynamoDB: {test_id}")
        
        return metadata
    
    def ingest_writing_test(self, material: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a writing test: store metadata + model answers."""
        test_id = material['test_id']
        
        metadata = {
            'test_id': test_id,
            'section': 'writing',
            'title': material.get('title', ''),
            'description': material.get('description', ''),
            'tasks_count': len(material.get('tasks', [])),
            'total_points': material.get('total_points', 9),
            'source': material['source'],
            'created_at': material.get('created_at', datetime.utcnow().isoformat()),
            'ingested_at': datetime.utcnow().isoformat(),
            'content': material
        }
        
        if not self.dry_run:
            if not self.dynamodb.put_item(metadata):
                raise Exception(f"Failed to write metadata to DynamoDB for test {test_id}")
        else:
            logger.info(f"[DRY RUN] Would write metadata to DynamoDB: {test_id}")
        
        return metadata
    
    def ingest_speaking_test(self, material: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a speaking test: store metadata + parts + rubrics."""
        test_id = material['test_id']
        
        metadata = {
            'test_id': test_id,
            'section': 'speaking',
            'title': material.get('title', ''),
            'description': material.get('description', ''),
            'parts_count': len(material.get('parts', [])),
            'total_points': material.get('total_points', 9),
            'source': material['source'],
            'created_at': material.get('created_at', datetime.utcnow().isoformat()),
            'ingested_at': datetime.utcnow().isoformat(),
            'content': material
        }
        
        if not self.dry_run:
            if not self.dynamodb.put_item(metadata):
                raise Exception(f"Failed to write metadata to DynamoDB for test {test_id}")
        else:
            logger.info(f"[DRY RUN] Would write metadata to DynamoDB: {test_id}")
        
        return metadata
