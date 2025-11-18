# IELTS Content Ingestion Tool

A Python CLI tool for ingesting verified IELTS exam materials into AWS (S3 + DynamoDB). Supports all four sections: Listening, Reading, Writing, and Speaking.

## Features

- **Schema Validation**: Pydantic-based schemas for all 4 IELTS sections
- **Pre-Upload Checks**: Audio format validation, file completeness, structure validation
- **AWS Integration**: Upload audio to S3, store metadata in DynamoDB
- **Batch Processing**: Ingest multiple test materials in a single manifest
- **Dry-Run Mode**: Validate without touching AWS
- **Example Manifests**: Ready-to-use JSON templates for each section

## Project Structure

```
tools/content-ingest/
├── ingest.py                  # Main CLI entry point
├── schema.py                  # Pydantic models for all sections
├── validators.py              # Pre-upload validation logic
├── aws_helpers.py             # S3, DynamoDB wrappers
├── pyproject.toml             # Dependencies and project config
├── README.md                  # This file
├── manifests/
│   ├── sample_listening.json  # Example Listening manifest
│   ├── sample_reading.json    # Example Reading manifest
│   ├── sample_writing.json    # Example Writing manifest
│   └── sample_speaking.json   # Example Speaking manifest
└── tests/
    ├── test_schema.py         # Schema validation tests
    ├── test_validators.py     # Validator tests
    └── test_ingest.py         # Integration tests
```

## Installation

### Prerequisites

- Python 3.9+
- AWS account with S3 and DynamoDB access
- `ffmpeg` installed (for audio validation)

### Setup

```bash
cd tools/content-ingest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .

# For development (with testing tools)
pip install -e ".[dev]"
```

### Configure AWS Credentials

```bash
# Option 1: AWS credentials file
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"

# Option 3: .env file (create at project root)
cat > .env << EOF
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
EOF
```

## Usage

### 1. Validate a Manifest (Dry Run)

```bash
python ingest.py manifests/sample_listening.json \
  --s3-bucket moe-exams \
  --dynamodb-table ielts_materials \
  --dry-run
```

Expected output:
```
✓ Manifest schema validation passed
✓ Manifest content validation passed
[DRY RUN] Would upload...
[DRY RUN] Would write metadata to DynamoDB...
```

### 2. Ingest to AWS

```bash
python ingest.py manifests/sample_listening.json \
  --s3-bucket moe-exams \
  --dynamodb-table ielts_materials \
  --region us-east-1
```

### 3. Ingest Multiple Sections

```bash
# Create a combined manifest or run separately:
python ingest.py manifests/sample_listening.json --s3-bucket moe-exams --dynamodb-table ielts_materials
python ingest.py manifests/sample_reading.json --s3-bucket moe-exams --dynamodb-table ielts_materials
python ingest.py manifests/sample_writing.json --s3-bucket moe-exams --dynamodb-table ielts_materials
python ingest.py manifests/sample_speaking.json --s3-bucket moe-exams --dynamodb-table ielts_materials
```

### 4. Check Help

```bash
python ingest.py --help
```

## Manifest Format

Each manifest is a JSON/YAML file with this structure:

```json
{
  "batch_id": "unique-batch-id",
  "batch_name": "Human-readable batch name",
  "materials": [
    {
      "material": {
        "section": "listening|reading|writing|speaking",
        "test_id": "unique-test-id",
        "title": "Test title",
        "description": "Optional description",
        ... section-specific fields ...
      }
    }
  ]
}
```

### Listening Manifest Example

```json
{
  "batch_id": "batch-001",
  "materials": [
    {
      "material": {
        "section": "listening",
        "test_id": "listening-001",
        "title": "Listening Test 1",
        "audio": {
          "filename": "listening-test-1.mp3",
          "duration_seconds": 180,
          "sample_rate": 44100
        },
        "transcript": {
          "full_text": "Full transcript text here..."
        },
        "questions": [
          {
            "question_id": "Q1",
            "question_type": "multiple_choice",
            "question_text": "What is the main topic?",
            "options": [
              {"option_id": "A", "text": "Option A"},
              ...
            ],
            "correct_answer_ids": ["A"]
          }
        ],
        "source": {
          "source_name": "IELTS.org",
          "license": "public_domain"
        }
      }
    }
  ]
}
```

See `manifests/sample_*.json` for complete examples for each section.

## Schema Reference

### Supported Question Types

- `multiple_choice`: Single or multiple correct answers
- `short_answer`: Free-form text (Listening/Reading)
- `sentence_completion`: Fill-in-the-blank
- `matching`: Match items to categories or passages
- `essay`: Extended writing (Writing task)
- `letter`: Letter/Email writing (Writing task)

### Exam Sections

- **Listening**: Audio file + transcript + questions (MCQ, short answer, matching)
- **Reading**: Multiple passages + questions (MCQ, short answer, matching)
- **Writing**: 2 Tasks (letter/report + essay) + rubrics for scoring
- **Speaking**: 3 Parts + rubrics for fluency, lexicon, grammar, pronunciation

### Rubric Structure

Each subjective section (Writing, Speaking) includes rubrics:

```json
{
  "criterion": "Task Achievement",
  "band_descriptors": {
    "9": "Fully accomplishes...",
    "8": "Sufficiently addresses...",
    ...
  },
  "weight": 0.25,
  "max_points": 9
}
```

## Testing

### Unit Tests

```bash
pytest tests/ -v
```

### With Coverage

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### Test a Single Module

```bash
pytest tests/test_schema.py -v
```

## DynamoDB Table Schema

Recommended table configuration:

```
Table Name: ielts_materials
Primary Key:
  - Partition Key: test_id (String)
  
Global Secondary Indexes (optional):
  - section-created_at-index
    - Partition Key: section (String)
    - Sort Key: created_at (String)
```

Create table via AWS CLI:

```bash
aws dynamodb create-table \
  --table-name ielts_materials \
  --attribute-definitions \
    AttributeName=test_id,AttributeType=S \
    AttributeName=section,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=test_id,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=section-created_at-index,Keys=[{AttributeName=section,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --billing-mode PAY_PER_REQUEST
```

Or use Terraform/CDK for IaC.

## Common Errors

### ffmpeg not found
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

### AWS credentials not configured
```bash
aws configure
# or set environment variables
export AWS_ACCESS_KEY_ID=...
```

### Audio validation fails
- Check audio format (support: mp3, wav, aac, m4a, flac)
- Check sample rate (must be 16kHz-48kHz)
- Ensure file exists at the specified path

### DynamoDB write fails
- Verify table exists
- Check IAM permissions (PutItem, GetItem on table)
- Verify table is not throttled

## Next Steps (Phase 2+)

1. **Scoring Logic** (`packages/functions/`):
   - Deterministic grading for Reading/Listening
   - Rule-based scoring for Writing (grammar, length, similarity)
   - ASR + feature extraction for Speaking

2. **Test Harness** (`tools/content-ingest/tests/`):
   - Benchmark tests with gold labels
   - Correlation/MAE metrics

3. **Admin UI** (optional):
   - Web interface for uploading approved materials
   - Preview and approve before ingestion

## License

MIT License - see LICENSE file

## Contributing

Submit issues and PRs to the main repository.

## Support

For issues or questions, contact the MOE EnglishProTool team.
