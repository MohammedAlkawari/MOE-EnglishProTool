#!/usr/bin/env python3
"""
IELTS exam material ingestion CLI.

Ingest verified IELTS materials:
  1. Parse manifest YAML/JSON
  2. Validate structure and assets
  3. Upload audio to S3
  4. Store metadata in DynamoDB

Usage:
    python ingest.py manifest.json --s3-bucket my-bucket --dynamodb-table exams --dry-run
    python ingest.py manifest.json --s3-bucket my-bucket --dynamodb-table exams
"""

import argparse
import json
import yaml
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from schema import IngestionManifest, ExamMaterial
from validators import ManifestValidator, AudioValidator, ValidationError
from aws_helpers import IngestionHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_manifest(manifest_path: str) -> dict:
    """Load manifest from JSON or YAML file."""
    path = Path(manifest_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    try:
        if path.suffix in {'.json', '.jsonl'}:
            with open(path) as f:
                return json.load(f)
        elif path.suffix in {'.yaml', '.yml'}:
            with open(path) as f:
                return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    except Exception as e:
        raise ValueError(f"Failed to parse manifest: {e}")


def validate_manifest_schema(manifest_dict: dict):
    """Validate manifest against Pydantic schema."""
    try:
        IngestionManifest(**manifest_dict)
        logger.info("✓ Manifest schema validation passed")
    except Exception as e:
        logger.error(f"✗ Manifest schema validation failed: {e}")
        raise


def validate_manifest_content(manifest_dict: dict, base_dir: str = '.'):
    """Validate manifest content (files, audio, etc.)."""
    errors = ManifestValidator.validate_manifest(manifest_dict, base_dir=base_dir)
    
    if errors:
        logger.error("✗ Manifest content validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
        raise ValidationError(f"Manifest validation failed with {len(errors)} error(s)")
    else:
        logger.info("✓ Manifest content validation passed")


def ingest_batch(
    manifest_path: str,
    s3_bucket: str,
    dynamodb_table: str,
    region: str = 'us-east-1',
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main ingestion workflow.
    """
    logger.info(f"Starting ingestion from {manifest_path}")
    logger.info(f"  S3 Bucket: {s3_bucket}")
    logger.info(f"  DynamoDB Table: {dynamodb_table}")
    logger.info(f"  Region: {region}")
    logger.info(f"  Dry Run: {dry_run}")
    
    # Load and validate manifest
    manifest_dict = load_manifest(manifest_path)
    manifest_dir = str(Path(manifest_path).parent)
    
    # Schema validation
    validate_manifest_schema(manifest_dict)
    
    # Content validation
    validate_manifest_content(manifest_dict, base_dir=manifest_dir)
    
    # Initialize ingestion helper
    helper = IngestionHelper(s3_bucket, dynamodb_table, region=region, dry_run=dry_run)
    
    batch_id = manifest_dict['batch_id']
    materials = manifest_dict['materials']
    
    results = {
        'batch_id': batch_id,
        'total_materials': len(materials),
        'ingested': [],
        'failed': []
    }
    
    # Ingest each material
    for i, material_wrapper in enumerate(materials):
        material = material_wrapper['material']
        section = material.get('section')
        test_id = material.get('test_id', f'unknown-{i}')
        
        try:
            logger.info(f"\n[{i+1}/{len(materials)}] Ingesting {section} test: {test_id}")
            
            if section == 'listening':
                # For listening, we need to upload audio
                audio = material['audio']
                audio_filename = audio.get('filename')
                audio_path = Path(manifest_dir) / audio_filename if audio_filename else None
                
                if not audio_path or not audio_path.exists():
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
                # Validate audio before upload
                is_valid, err_msg, metadata = AudioValidator.validate_audio_file(str(audio_path))
                if not is_valid:
                    raise ValidationError(f"Audio validation failed: {err_msg}")
                
                result = helper.ingest_listening_test(material, str(audio_path))
            
            elif section == 'reading':
                result = helper.ingest_reading_test(material)
            
            elif section == 'writing':
                result = helper.ingest_writing_test(material)
            
            elif section == 'speaking':
                result = helper.ingest_speaking_test(material)
            
            else:
                raise ValueError(f"Unknown section: {section}")
            
            logger.info(f"  ✓ Ingested successfully: {test_id}")
            results['ingested'].append({
                'test_id': test_id,
                'section': section,
                'result': result
            })
        
        except Exception as e:
            logger.error(f"  ✗ Ingestion failed: {str(e)}")
            results['failed'].append({
                'test_id': test_id,
                'section': section,
                'error': str(e)
            })
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Ingestion Summary")
    logger.info(f"{'='*60}")
    logger.info(f"Batch ID: {batch_id}")
    logger.info(f"Total: {results['total_materials']}")
    logger.info(f"Ingested: {len(results['ingested'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    
    if results['failed']:
        logger.warning("\nFailed Items:")
        for item in results['failed']:
            logger.warning(f"  - {item['section']}/{item['test_id']}: {item['error']}")
    
    if dry_run:
        logger.info("\n[DRY RUN] No data was actually ingested to AWS.")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='IELTS exam material ingestion CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s manifest.json --s3-bucket moe-exams --dynamodb-table ielts_materials --dry-run
  %(prog)s manifest.json --s3-bucket moe-exams --dynamodb-table ielts_materials --region us-west-2
  %(prog)s manifest.yaml --s3-bucket moe-exams --dynamodb-table ielts_materials
        '''
    )
    
    parser.add_argument('manifest', help='Path to manifest file (JSON or YAML)')
    parser.add_argument('--s3-bucket', required=True, help='S3 bucket name')
    parser.add_argument('--dynamodb-table', required=True, help='DynamoDB table name')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--dry-run', action='store_true', help='Validate without uploading to AWS')
    
    args = parser.parse_args()
    
    try:
        result = ingest_batch(
            args.manifest,
            args.s3_bucket,
            args.dynamodb_table,
            region=args.region,
            dry_run=args.dry_run
        )
        
        # Exit with status based on failures
        if result['failed']:
            sys.exit(1)
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
