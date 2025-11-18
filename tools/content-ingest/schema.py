"""
Canonical Pydantic schema for IELTS exam materials across all 4 sections.
Supports Listening, Reading, Writing, and Speaking with unified metadata.
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ============================================================================
# Enums
# ============================================================================

class ExamSection(str, Enum):
    """IELTS exam sections."""
    LISTENING = "listening"
    READING = "reading"
    WRITING = "writing"
    SPEAKING = "speaking"


class QuestionType(str, Enum):
    """Question types across sections."""
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    MATCHING = "matching"
    SENTENCE_COMPLETION = "sentence_completion"
    ESSAY = "essay"
    LETTER = "letter"
    CONVERSATION = "conversation"
    INDIVIDUAL_LONG_TURN = "individual_long_turn"


class BandLevel(str, Enum):
    """IELTS band levels."""
    BAND_1 = "1"
    BAND_2 = "2"
    BAND_3 = "3"
    BAND_4 = "4"
    BAND_5 = "5"
    BAND_6 = "6"
    BAND_7 = "7"
    BAND_8 = "8"
    BAND_9 = "9"


class CEFRLevel(str, Enum):
    """CEFR levels mapped to IELTS bands."""
    A1 = "A1"  # 1-2
    A2 = "A2"  # 2-3
    B1 = "B1"  # 4-5
    B2 = "B2"  # 6-7
    C1 = "C1"  # 7-8
    C2 = "C2"  # 8-9


# ============================================================================
# Common Models
# ============================================================================

class Rubric(BaseModel):
    """Scoring rubric for subjective tasks (Writing, Speaking)."""
    criterion: str = Field(..., description="e.g., 'Task Achievement', 'Lexical Range'")
    band_descriptors: Dict[str, str] = Field(
        ..., 
        description="Mapping from band level to descriptor. e.g., {'9': 'Fully achieves...', '8': 'Achieves...', ...}"
    )
    weight: float = Field(default=1.0, description="Weight in overall score (0.0-1.0)")
    max_points: int = Field(default=9, description="Max points for this criterion")


class Asset(BaseModel):
    """Reference to an asset stored in S3."""
    s3_key: str = Field(..., description="S3 object key (path) for this asset")
    filename: str = Field(..., description="Original filename for reference")
    content_type: str = Field(default="application/octet-stream", description="MIME type")
    size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    uploaded_at: Optional[str] = Field(default=None, description="ISO timestamp of upload")


class QuestionBase(BaseModel):
    """Base model for a question."""
    question_id: str = Field(..., description="Unique ID for this question within the test")
    question_type: QuestionType
    question_text: str = Field(..., description="The question stem or prompt")
    description: Optional[str] = Field(default=None, description="Additional context or instruction")


class AnswerOption(BaseModel):
    """Multiple choice / option selection answer."""
    option_id: str = Field(..., description="A, B, C, D, etc.")
    text: str


class MCQQuestion(QuestionBase):
    """Multiple choice question."""
    question_type: QuestionType = Field(default=QuestionType.MULTIPLE_CHOICE)
    options: List[AnswerOption]
    correct_answer_ids: List[str] = Field(..., description="List of correct option IDs (usually 1, but can support multiple)")


class ShortAnswerQuestion(QuestionBase):
    """Short answer question (fill-in-the-blank, etc.)."""
    question_type: QuestionType = Field(default=QuestionType.SHORT_ANSWER)
    correct_answers: List[str] = Field(..., description="Acceptable answers (can be multiple variants)")
    max_words: Optional[int] = Field(default=None, description="Max words in answer")


class MatchingQuestion(QuestionBase):
    """Matching question (e.g., match statements to paragraphs)."""
    question_type: QuestionType = Field(default=QuestionType.MATCHING)
    items: List[Dict[str, str]] = Field(..., description="Items to match, e.g., [{'id': '1', 'text': '...'}, ...]")
    matches: Dict[str, str] = Field(..., description="Mapping from item_id to correct match, e.g., {'1': 'A', '2': 'B'}")


class SourceMetadata(BaseModel):
    """Provenance and licensing info."""
    source_name: str = Field(..., description="e.g., 'IELTS.org', 'British Council', 'Synthetic'")
    source_url: Optional[str] = Field(default=None)
    license: str = Field(default="public_domain", description="e.g., 'public_domain', 'CC-BY-4.0', 'proprietary'")
    copyright_holder: Optional[str] = Field(default=None)
    created_date: Optional[str] = Field(default=None, description="ISO date")
    approved_by: Optional[str] = Field(default=None, description="Admin or curator who approved this")
    notes: Optional[str] = Field(default=None)


# ============================================================================
# LISTENING Section
# ============================================================================

class ListeningAudio(BaseModel):
    """Audio asset for listening section."""
    s3_key: str = Field(..., description="S3 object key for audio file")
    filename: str = Field(..., description="Original audio filename")
    duration_seconds: float = Field(..., description="Duration of audio in seconds")
    sample_rate: int = Field(default=44100, description="Sample rate in Hz")
    format: str = Field(default="mp3", description="Audio format (mp3, wav, etc.)")


class ListeningTranscript(BaseModel):
    """Transcript of listening audio."""
    full_text: str = Field(..., description="Complete transcript")
    timings: Optional[Dict[str, float]] = Field(
        default=None,
        description="Word/phrase timings, e.g., {'0:00-0:05': 'Hello everyone...'}"
    )


class ListeningTest(BaseModel):
    """Complete listening test/section."""
    section: ExamSection = Field(default=ExamSection.LISTENING)
    test_id: str = Field(..., description="Unique test/section ID")
    title: str = Field(..., description="e.g., 'Listening Test 1'")
    description: Optional[str] = Field(default=None)
    
    audio: ListeningAudio
    transcript: ListeningTranscript
    
    questions: List[Union[MCQQuestion, ShortAnswerQuestion, MatchingQuestion]] = Field(
        ..., description="List of questions for this section"
    )
    
    total_points: int = Field(default=40, description="Total points in section")
    duration_seconds: int = Field(default=30, description="Time allowed (minutes converted to seconds)")
    
    source: SourceMetadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field(default="1.0")


# ============================================================================
# READING Section
# ============================================================================

class ReadingPassage(BaseModel):
    """A reading passage."""
    passage_id: str = Field(..., description="Unique ID within test")
    title: str = Field(..., description="Title of passage/article")
    text: str = Field(..., description="Full passage text")
    word_count: int = Field(..., description="Word count of passage")
    source_url: Optional[str] = Field(default=None)


class ReadingTest(BaseModel):
    """Complete reading test/section."""
    section: ExamSection = Field(default=ExamSection.READING)
    test_id: str = Field(..., description="Unique test/section ID")
    title: str = Field(..., description="e.g., 'Reading Test 1'")
    description: Optional[str] = Field(default=None)
    
    passages: List[ReadingPassage]
    questions: List[Union[MCQQuestion, ShortAnswerQuestion, MatchingQuestion]] = Field(
        ..., description="Questions linked to passages (passage_id in question_text or metadata)"
    )
    
    total_points: int = Field(default=40)
    duration_seconds: int = Field(default=60 * 60, description="Typically 60 minutes")
    
    source: SourceMetadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field(default="1.0")


# ============================================================================
# WRITING Section
# ============================================================================

class WritingTask(BaseModel):
    """A writing task (Task 1 or Task 2)."""
    task_id: str = Field(..., description="'1' or '2'")
    prompt: str = Field(..., description="The writing prompt/instruction")
    task_type: str = Field(..., description="'letter', 'report', 'diagram', 'essay', etc.")
    word_count_min: int = Field(default=150, description="Min words (Task 1: 150, Task 2: 250)")
    word_count_recommended: int = Field(default=250)
    time_minutes: int = Field(default=20, description="Recommended time")
    
    band_model_answers: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Example answers for different bands. e.g., [{'band': '9', 'text': '...'}, {'band': '7', 'text': '...'}]"
    )


class WritingRubrics(BaseModel):
    """Rubrics for writing evaluation."""
    rubrics: List[Rubric] = Field(
        ...,
        description="List of criteria (Task Achievement, Coherence & Cohesion, Lexical Resource, Grammatical Accuracy)"
    )


class WritingTest(BaseModel):
    """Complete writing test/section."""
    section: ExamSection = Field(default=ExamSection.WRITING)
    test_id: str = Field(..., description="Unique test ID")
    title: str = Field(..., description="e.g., 'Writing Test 1'")
    description: Optional[str] = Field(default=None)
    
    tasks: List[WritingTask] = Field(..., description="Usually 2 tasks")
    rubrics: WritingRubrics
    
    total_points: int = Field(default=9, description="Band score (9-1)")
    duration_seconds: int = Field(default=60 * 60, description="Typically 60 minutes total")
    
    source: SourceMetadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field(default="1.0")


# ============================================================================
# SPEAKING Section
# ============================================================================

class SpeakingPart(BaseModel):
    """A part of the speaking test (Part 1, 2, or 3)."""
    part_id: str = Field(..., description="'1', '2', or '3'")
    duration_seconds: int = Field(..., description="Duration of this part")
    description: str = Field(..., description="Description of what happens in this part")
    prompts: List[str] = Field(..., description="Questions or prompts for this part")
    follow_up_prompts: Optional[List[str]] = Field(default=None, description="Follow-up questions (esp. for Part 1 and 3)")


class SpeakingRubrics(BaseModel):
    """Rubrics for speaking evaluation (fluency, lexicon, grammar, pronunciation, task response)."""
    rubrics: List[Rubric] = Field(
        ...,
        description="Usually 4 criteria: Fluency & Coherence, Lexical Resource, Grammatical Accuracy, Pronunciation"
    )


class SpeakingTest(BaseModel):
    """Complete speaking test/section."""
    section: ExamSection = Field(default=ExamSection.SPEAKING)
    test_id: str = Field(..., description="Unique test ID")
    title: str = Field(..., description="e.g., 'Speaking Test 1'")
    description: Optional[str] = Field(default=None)
    
    parts: List[SpeakingPart] = Field(..., description="Parts 1, 2, 3")
    rubrics: SpeakingRubrics
    
    total_points: int = Field(default=9, description="Band score (9-1)")
    duration_seconds: int = Field(default=11 * 60, description="Typically 11-14 minutes")
    
    source: SourceMetadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field(default="1.0")


# ============================================================================
# Unified Test Model
# ============================================================================

class ExamMaterial(BaseModel):
    """Wrapper for any exam material (flexible union type)."""
    material: Union[ListeningTest, ReadingTest, WritingTest, SpeakingTest] = Field(
        ..., description="The test material (one of the four sections)"
    )

    class Config:
        use_enum_values = False


# ============================================================================
# Ground Truth / Labels for Validation
# ============================================================================

class StudentSubmission(BaseModel):
    """A student's response to an exam."""
    submission_id: str
    test_id: str
    section: ExamSection
    student_id: str
    submitted_at: str  # ISO timestamp
    responses: Dict[str, Any] = Field(..., description="Question ID -> answer mapping")
    # For listening/reading: correct/incorrect flags
    # For writing: submitted text
    # For speaking: submitted audio S3 key


class HumanLabel(BaseModel):
    """Human rater's label (for validation/training)."""
    label_id: str
    submission_id: str
    section: ExamSection
    rater_id: str
    rated_at: str  # ISO timestamp
    
    # For subjective sections (Writing, Speaking)
    band_score: Optional[BandLevel] = Field(default=None)
    criterion_scores: Optional[Dict[str, int]] = Field(default=None, description="Criterion -> score mapping")
    feedback: Optional[str] = Field(default=None, description="Qualitative feedback")
    
    # For objective sections (Listening, Reading)
    accuracy: Optional[float] = Field(default=None, description="Fraction correct (0.0-1.0)")
    correct_count: Optional[int] = Field(default=None)
    total_count: Optional[int] = Field(default=None)


# ============================================================================
# Ingestion Request
# ============================================================================

class IngestionManifest(BaseModel):
    """Manifest for ingesting a batch of exam materials."""
    batch_id: str = Field(..., description="Unique ID for this batch")
    batch_name: str = Field(..., description="Human-readable name")
    materials: List[ExamMaterial] = Field(..., description="List of exam materials to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default=None)
