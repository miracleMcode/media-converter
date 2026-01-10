import numpy as np
import matplotlib.pyplot as plt
from moviepy.editor import AudioFileClip, ImageSequenceClip
import os

AUDIO_PATH = "input/sample.mp3"
OUTPUT_VIDEO = "output/audio_video.mp4"
FPS = 24

def audio_to_video(audio_path, output_path):
    audio = AudioFileClip(audio_path)

    # Get audio samples
    samples = audio.to_soundarray(fps=44100)
    samples = samples.mean(axis=1)  # convert to mono

    duration = audio.duration
    total_frames = int(duration * FPS)
    chunk_size = len(samples) // total_frames

    frames = []
    os.makedirs("frames", exist_ok=True)

    for i in range(total_frames):
        start = i * chunk_size
        end = start + chunk_size
        chunk = samples[start:end]

        plt.figure(figsize=(6, 4))
        plt.plot(chunk, color="blue")
        plt.ylim(-1, 1)
        plt.axis("off")

        frame_path = f"frames/frame_{i}.png"
        plt.savefig(frame_path)
        plt.close()

        frames.append(frame_path)

    video = ImageSequenceClip(frames, fps=FPS)
    final = video.set_audio(audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

    print("✅ Audio converted to video successfully!")

if __name__ == "__main__":
    audio_to_video(AUDIO_PATH, OUTPUT_VIDEO)
