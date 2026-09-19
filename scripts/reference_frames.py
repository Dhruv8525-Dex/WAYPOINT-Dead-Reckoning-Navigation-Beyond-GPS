"""Create a timestamped contact sheet from the user-supplied design recording."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.tools/media').resolve()))
import imageio_ffmpeg
from PIL import Image, ImageDraw
video = r'C:\Users\dhruv\Videos\Screen Recordings\Screen Recording 2026-09-09 053331.mp4'
reader = imageio_ffmpeg.read_frames(video, pix_fmt='rgb24')
meta = next(reader)
print(meta)
width, height = meta['size']
interval = max(1, round(meta['fps']))
frames = []
for index, frame in enumerate(reader):
    if index % interval == 0:
        im = Image.frombytes('RGB', (width, height), frame)
        im.thumbnail((500, 320))
        frames.append((index / meta['fps'], im))
sheet = Image.new('RGB', (1500, ((len(frames)+2)//3)*355), '#eeeeee')
draw = ImageDraw.Draw(sheet)
for i,(seconds,im) in enumerate(frames):
    x,y=(i%3)*500,(i//3)*355
    sheet.paste(im,(x,y+25))
    draw.text((x+10,y+5),f'{seconds:05.1f} s',fill='black')
Path('artifacts/redesign').mkdir(parents=True,exist_ok=True)
sheet.save('artifacts/redesign/reference-timeline.jpg')
print('Frames:',len(frames))
