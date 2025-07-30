# editor.py
from moviepy.editor import VideoFileClip, concatenate_videoclips

class VideoEditor:
    def __init__(self):
        self.clips = []

    def add_clip(self, filepath, start_time=0, end_time=None):
        clip = VideoFileClip(filepath)
        if end_time is not None:
            clip = clip.subclip(start_time, end_time)
        elif start_time > 0:
            clip = clip.subclip(start_time)
        self.clips.append(clip)

    def export(self, output_path):
        final = concatenate_videoclips(self.clips)
        final.write_videofile(output_path, codec='libx264')
