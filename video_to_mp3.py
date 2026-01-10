from moviepy.editor import VideoFileClip
import os

INPUT_VIDEO = "input/sample.mp4"
OUTPUT_AUDIO = "output/output_audio.mp3"

def video_to_mp3(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    video.close()
    print("✅ Video converted to MP3 successfully!")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    video_to_mp3(INPUT_VIDEO, OUTPUT_AUDIO)
