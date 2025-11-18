"""
Validators for exam materials before ingestion.
Checks: file existence, audio format, schema correctness, content constraints.
"""

import os
import json
from pathlib import Path
from typing import Tuple, List, Optional
import subprocess


class ValidationError(Exception):
    """Custom validation error."""
    pass


class AudioValidator:
    """Validate audio files (format, duration, sample rate)."""
    
    SUPPORTED_FORMATS = {'mp3', 'wav', 'aac', 'm4a', 'flac'}
    MIN_SAMPLE_RATE = 16000
    MAX_SAMPLE_RATE = 48000
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, str, dict]:
        """
        Validate audio file using ffprobe.
        Returns: (is_valid, error_message, metadata)
        """
        if not os.path.exists(file_path):
            return False, f"Audio file not found: {file_path}", {}
        
        try:
            result = subprocess.run(
                [
                    'ffprobe', '-v', 'error', '-show_format', '-show_streams',
                    '-print_json', file_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, f"ffprobe error: {result.stderr}", {}
            
            probe_data = json.loads(result.stdout)
            
            # Extract metadata
            fmt = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
            if not audio_stream:
                return False, "No audio stream found", {}
            
            # Check format
            file_ext = Path(file_path).suffix.lstrip('.').lower()
            if file_ext not in AudioValidator.SUPPORTED_FORMATS:
                return False, f"Unsupported format: {file_ext}. Supported: {AudioValidator.SUPPORTED_FORMATS}", {}
            
            # Extract metadata
            duration = float(fmt.get('duration', 0))
            sample_rate = int(audio_stream.get('sample_rate', 0))
            codec = audio_stream.get('codec_name', 'unknown')
            
            # Validate
            if sample_rate < AudioValidator.MIN_SAMPLE_RATE or sample_rate > AudioValidator.MAX_SAMPLE_RATE:
                return False, f"Sample rate {sample_rate} out of range ({AudioValidator.MIN_SAMPLE_RATE}-{AudioValidator.MAX_SAMPLE_RATE})", {}
            
            metadata = {
                'duration_seconds': duration,
                'sample_rate': sample_rate,
                'codec': codec,
                'size_bytes': os.path.getsize(file_path)
            }
            
            return True, "", metadata
        
        except subprocess.TimeoutExpired:
            return False, "ffprobe timeout", {}
        except Exception as e:
            return False, f"ffprobe exception: {str(e)}", {}


class ManifestValidator:
    """Validate manifest structure and content."""
    
    @staticmethod
    def validate_manifest(manifest_dict: dict, base_dir: Optional[str] = None) -> List[str]:
        """
        Validate manifest structure.
        Returns: list of error messages (empty if valid).
        """
        errors = []
        
        # Check required fields
        if 'batch_id' not in manifest_dict:
            errors.append("Missing 'batch_id' in manifest")
        if 'materials' not in manifest_dict or not isinstance(manifest_dict.get('materials'), list):
            errors.append("Missing or invalid 'materials' in manifest (must be list)")
            return errors
        
        materials = manifest_dict['materials']
        
        # Validate each material
        for i, material_wrapper in enumerate(materials):
            if 'material' not in material_wrapper:
                errors.append(f"Material {i}: missing 'material' key")
                continue
            
            material = material_wrapper['material']
            section = material.get('section')
            test_id = material.get('test_id', f'unknown-{i}')
            
            # Section-specific validation
            if section == 'listening':
                errors.extend(ManifestValidator._validate_listening(material, i, base_dir))
            elif section == 'reading':
                errors.extend(ManifestValidator._validate_reading(material, i, base_dir))
            elif section == 'writing':
                errors.extend(ManifestValidator._validate_writing(material, i, base_dir))
            elif section == 'speaking':
                errors.extend(ManifestValidator._validate_speaking(material, i, base_dir))
            else:
                errors.append(f"Material {i} ({test_id}): unknown section '{section}'")
        
        return errors
    
    @staticmethod
    def _validate_listening(material: dict, idx: int, base_dir: Optional[str]) -> List[str]:
        """Validate listening material."""
        errors = []
        test_id = material.get('test_id', f'listening-{idx}')
        prefix = f"Listening {idx} ({test_id})"
        
        # Check audio
        audio = material.get('audio')
        if not audio:
            errors.append(f"{prefix}: missing 'audio'")
        else:
            audio_file = audio.get('filename')
            if base_dir and audio_file:
                full_path = os.path.join(base_dir, audio_file)
                is_valid, err_msg, metadata = AudioValidator.validate_audio_file(full_path)
                if not is_valid:
                    errors.append(f"{prefix}: audio validation failed: {err_msg}")
        
        # Check transcript
        transcript = material.get('transcript')
        if not transcript or 'full_text' not in transcript:
            errors.append(f"{prefix}: missing or invalid 'transcript'")
        
        # Check questions
        questions = material.get('questions', [])
        if len(questions) == 0:
            errors.append(f"{prefix}: no questions found")
        
        return errors
    
    @staticmethod
    def _validate_reading(material: dict, idx: int, base_dir: Optional[str]) -> List[str]:
        """Validate reading material."""
        errors = []
        test_id = material.get('test_id', f'reading-{idx}')
        prefix = f"Reading {idx} ({test_id})"
        
        passages = material.get('passages', [])
        if len(passages) == 0:
            errors.append(f"{prefix}: no passages found")
        
        questions = material.get('questions', [])
        if len(questions) == 0:
            errors.append(f"{prefix}: no questions found")
        
        return errors
    
    @staticmethod
    def _validate_writing(material: dict, idx: int, base_dir: Optional[str]) -> List[str]:
        """Validate writing material."""
        errors = []
        test_id = material.get('test_id', f'writing-{idx}')
        prefix = f"Writing {idx} ({test_id})"
        
        tasks = material.get('tasks', [])
        if len(tasks) == 0:
            errors.append(f"{prefix}: no tasks found")
        
        rubrics = material.get('rubrics')
        if not rubrics:
            errors.append(f"{prefix}: missing 'rubrics'")
        
        return errors
    
    @staticmethod
    def _validate_speaking(material: dict, idx: int, base_dir: Optional[str]) -> List[str]:
        """Validate speaking material."""
        errors = []
        test_id = material.get('test_id', f'speaking-{idx}')
        prefix = f"Speaking {idx} ({test_id})"
        
        parts = material.get('parts', [])
        if len(parts) == 0:
            errors.append(f"{prefix}: no parts found")
        
        rubrics = material.get('rubrics')
        if not rubrics:
            errors.append(f"{prefix}: missing 'rubrics'")
        
        return errors
