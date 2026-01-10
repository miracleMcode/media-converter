from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import logging
from datetime import datetime
import subprocess
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'aac', 'm4a'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    """Check if all dependencies are available"""
    return jsonify({
        'ffmpeg': check_ffmpeg()
    })

@app.route('/convert/video-to-mp3', methods=['POST'])
def video_to_mp3():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv'}), 400
    
    if not check_ffmpeg():
        return jsonify({'error': 'FFmpeg not installed. Please install FFmpeg.'}), 500
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Converting video: {filename}")
        
        # Run conversion
        output_filename = Path(filename).stem + f'_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3'
        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Convert using FFmpeg
        cmd = [
            'ffmpeg',
            '-i', filepath,
            '-q:a', '9',
            '-n',
            output_filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify({'error': f'Conversion failed: {result.stderr}'}), 500
        
        logger.info(f"Conversion successful: {output_filename}")
        
        # Clean up upload
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'url': f'/download/{output_filename}'
        })
    
    except Exception as e:
        logger.error(f"Error in video_to_mp3: {str(e)}")
        try:
            os.remove(filepath)
        except:
            pass
        return jsonify({'error': str(e)}), 500

@app.route('/convert/audio-to-video', methods=['POST'])
def audio_to_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp3, wav, aac, m4a'}), 400
    
    if not check_ffmpeg():
        return jsonify({'error': 'FFmpeg not installed. Please install FFmpeg.'}), 500
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Converting audio to video: {filename}")
        
        # Run conversion
        output_filename = Path(filename).stem + f'_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        try:
            import numpy as np
            import matplotlib.pyplot as plt
            from moviepy.editor import ImageSequenceClip, AudioFileClip
            
            # Load audio
            audio_clip = AudioFileClip(filepath)
            duration = audio_clip.duration
            fps = 30
            total_frames = int(duration * fps)
            
            # Extract audio samples for waveform visualization
            wav_path = os.path.splitext(filepath)[0] + '_temp.wav'
            
            extract_cmd = [
                'ffmpeg', '-i', filepath,
                '-acodec', 'pcm_s16le',
                '-ar', '22050',
                '-ac', '1',
                '-n',
                wav_path
            ]
            subprocess.run(extract_cmd, capture_output=True)
            
            # Load waveform data
            import wave
            with wave.open(wav_path, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
            
            # Normalize
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Generate animated frames
            frames_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'frames_temp')
            os.makedirs(frames_dir, exist_ok=True)
            
            samples_per_frame = len(audio_data) // total_frames
            window_size = min(1000, len(audio_data) // 10)  # Show last 1000 samples or 10% of audio
            
            for frame_idx in range(total_frames):
                start_idx = max(0, frame_idx * samples_per_frame - window_size)
                end_idx = min(len(audio_data), frame_idx * samples_per_frame + window_size)
                
                current_chunk = audio_data[start_idx:end_idx]
                
                # Create frame
                fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=100)
                ax.set_facecolor('#1a1a1a')
                fig.patch.set_facecolor('#000000')
                
                # Plot waveform
                x = np.linspace(0, len(current_chunk), len(current_chunk))
                ax.fill_between(x, 0, current_chunk, color='#00ff00', alpha=0.7)
                ax.plot(x, current_chunk, color='#00ff00', linewidth=0.5)
                
                # Add progress indicator
                progress_text = f'{frame_idx / total_frames * 100:.1f}%'
                ax.text(0.98, 0.95, progress_text, transform=ax.transAxes, 
                       fontsize=20, color='#00ff00', ha='right', va='top',
                       fontfamily='monospace')
                
                ax.set_xlim(0, len(current_chunk))
                ax.set_ylim(-1.2, 1.2)
                ax.axis('off')
                
                plt.tight_layout(pad=0)
                frame_path = os.path.join(frames_dir, f'frame_{frame_idx:06d}.png')
                plt.savefig(frame_path, facecolor='#000000', bbox_inches='tight', 
                           pad_inches=0, dpi=100)
                plt.close()
            
            # Create video from frames using ffmpeg
            frames_pattern = os.path.join(frames_dir, 'frame_%06d.png')
            video_cmd = [
                'ffmpeg',
                '-framerate', str(fps),
                '-i', frames_pattern,
                '-i', filepath,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                '-y',
                output_filepath
            ]
            
            result = subprocess.run(video_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(result.stderr)
            
            logger.info(f"Conversion successful: {output_filename}")
            
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            raise
        
        # Clean up
        try:
            os.remove(filepath)
        except:
            pass
        try:
            import shutil
            frames_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'frames_temp')
            if os.path.exists(frames_dir):
                shutil.rmtree(frames_dir)
        except:
            pass
        try:
            os.remove(wav_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'url': f'/download/{output_filename}'
        })
    
    except Exception as e:
        logger.error(f"Error in audio_to_video: {str(e)}")
        try:
            os.remove(filepath)
        except:
            pass
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum: 500MB'}), 413

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Flask Media Converter...")
    # For production: gunicorn will handle this
    # For local development: use debug mode
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), use_reloader=False)
