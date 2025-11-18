"""
Unit tests for schema validation.
"""

import pytest
from pydantic import ValidationError
from schema import (
    ExamSection, QuestionType, BandLevel, CEFRLevel,
    MCQQuestion, ShortAnswerQuestion, MatchingQuestion,
    ListeningTest, ReadingTest, WritingTest, SpeakingTest,
    SourceMetadata, Rubric, AnswerOption
)


class TestExamSection:
    """Test ExamSection enum."""
    
    def test_valid_sections(self):
        assert ExamSection.LISTENING.value == "listening"
        assert ExamSection.READING.value == "reading"
        assert ExamSection.WRITING.value == "writing"
        assert ExamSection.SPEAKING.value == "speaking"


class TestQuestionTypes:
    """Test question type enums."""
    
    def test_valid_question_types(self):
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.SHORT_ANSWER.value == "short_answer"
        assert QuestionType.MATCHING.value == "matching"
        assert QuestionType.ESSAY.value == "essay"


class TestMCQQuestion:
    """Test MCQ question model."""
    
    def test_valid_mcq(self):
        q = MCQQuestion(
            question_id="Q1",
            question_text="What is the capital of France?",
            options=[
                AnswerOption(option_id="A", text="London"),
                AnswerOption(option_id="B", text="Paris"),
                AnswerOption(option_id="C", text="Berlin"),
            ],
            correct_answer_ids=["B"]
        )
        assert q.question_id == "Q1"
        assert len(q.options) == 3
        assert q.correct_answer_ids == ["B"]
    
    def test_mcq_missing_options(self):
        with pytest.raises(ValidationError):
            MCQQuestion(
                question_id="Q1",
                question_text="What is the capital of France?",
                correct_answer_ids=["B"]
                # missing options
            )


class TestShortAnswerQuestion:
    """Test short answer question model."""
    
    def test_valid_short_answer(self):
        q = ShortAnswerQuestion(
            question_id="Q2",
            question_text="How many semesters does the program have?",
            correct_answers=["four", "4"],
            max_words=3
        )
        assert q.question_id == "Q2"
        assert len(q.correct_answers) == 2
    
    def test_short_answer_missing_correct_answers(self):
        with pytest.raises(ValidationError):
            ShortAnswerQuestion(
                question_id="Q2",
                question_text="How many semesters?",
                max_words=3
                # missing correct_answers
            )


class TestSourceMetadata:
    """Test source metadata."""
    
    def test_valid_source(self):
        source = SourceMetadata(
            source_name="IELTS.org",
            license="public_domain"
        )
        assert source.source_name == "IELTS.org"
        assert source.license == "public_domain"
    
    def test_missing_source_name(self):
        with pytest.raises(ValidationError):
            SourceMetadata(
                license="public_domain"
                # missing source_name
            )


class TestRubric:
    """Test rubric model."""
    
    def test_valid_rubric(self):
        rubric = Rubric(
            criterion="Task Achievement",
            band_descriptors={
                "9": "Fully achieves",
                "8": "Achieves",
                "7": "Adequately achieves"
            },
            weight=0.25
        )
        assert rubric.criterion == "Task Achievement"
        assert rubric.weight == 0.25
    
    def test_rubric_default_weight(self):
        rubric = Rubric(
            criterion="Fluency",
            band_descriptors={"9": "Highly fluent"}
        )
        assert rubric.weight == 1.0


class TestBandLevels:
    """Test band level enum."""
    
    def test_valid_bands(self):
        assert BandLevel.BAND_9.value == "9"
        assert BandLevel.BAND_1.value == "1"
        assert BandLevel.BAND_5.value == "5"


class TestCEFRLevels:
    """Test CEFR level enum."""
    
    def test_valid_cefr_levels(self):
        assert CEFRLevel.A1.value == "A1"
        assert CEFRLevel.B2.value == "B2"
        assert CEFRLevel.C1.value == "C1"


# Integration tests for full test models would go here
# (Listening, Reading, Writing, Speaking)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
