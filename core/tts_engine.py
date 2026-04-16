"""
ElevenLabs TTS Module
Generates audio from script segments
"""

import os
import re
import time
from typing import List, Dict
from elevenlabs import ElevenLabs, VoiceSettings
from elevenlabs.client import ElevenLabs as ElevenLabsClient


class TTSEngine:
    """Text-to-Speech using ElevenLabs API"""
    
    def __init__(self, api_key: str, voice_id: str):
        self.client = ElevenLabsClient(api_key=api_key)
        self.voice_id = voice_id
        
    def segment_script(self, script: str, words_per_segment: int = 150) -> List[Dict]:
        """
        Split script into segments based on word count
        Args:
            script: Full script text
            words_per_segment: Target words per segment (e.g., 150 = ~1 minute)
        """
        words_per_segment = int(words_per_segment)
        
        # Split by sentences for natural breaks
        sentences = re.split(r'(?<=[.!?])\s+', script)
        
        segments = []
        current_segment = []
        current_word_count = 0
        segment_number = 1
        
        for sentence in sentences:
            word_count = len(sentence.split())
            
            if current_word_count + word_count > words_per_segment and current_segment:
                # Save current segment
                segment_text = ' '.join(current_segment)
                segments.append({
                    "number": segment_number,
                    "text": segment_text.strip(),
                    "word_count": current_word_count,
                    "estimated_seconds": (current_word_count / 150) * 60
                })
                
                # Start new segment
                segment_number += 1
                current_segment = [sentence]
                current_word_count = word_count
            else:
                current_segment.append(sentence)
                current_word_count += word_count
        
        # Add remaining segment
        if current_segment:
            segment_text = ' '.join(current_segment)
            segments.append({
                "number": segment_number,
                "text": segment_text.strip(),
                "word_count": current_word_count,
                "estimated_seconds": (current_word_count / 150) * 60
            })
        
        print(f"Script segmented into {len(segments)} parts")
        for seg in segments:
            print(f"  Segment {seg['number']}: ~{seg['estimated_seconds']:.0f}s, {seg['word_count']} words")
        
        return segments
    
    def generate_audio(self, text: str, output_path: str) -> bool:
        """Generate audio for single segment"""
        try:
            print(f"Generating audio: {output_path}")
            
            # Generate with streaming
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            # Save to file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
            
            print(f"Audio saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return False
    
    def generate_all_audio(self, segments: List[Dict], output_folder: str):
        """Generate audio for all segments"""
        successful = 0
        failed = 0
        
        for segment in segments:
            output_path = os.path.join(output_folder, f"{segment['number']:03d}.mp3")
            
            print(f"\n[{segment['number']}/{len(segments)}] Generating audio...")
            
            if self.generate_audio(segment['text'], output_path):
                successful += 1
            else:
                failed += 1
            
            # Rate limiting - respect ElevenLabs limits
            time.sleep(1)
        
        print(f"\n{'='*50}")
        print(f"TTS complete: {successful} successful, {failed} failed")
        print(f"{'='*50}")
        
        return successful, failed
