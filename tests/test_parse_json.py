""" Test parsing JSON transcript """

from core.transcript_parser import parse_transcript

if __name__ == "__main__":
    lines = parse_transcript(audio_path=None, srt_path="Time_Traveler_Pensions,_Quantum_Minds,_and_the_ADHD_Spiritual/transcript.json")
    print(f"Parsed {len(lines)} lines from JSON transcript")