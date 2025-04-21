#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import glob
import json
import signal
import shutil
import termios
import tty
import threading
import argparse
from PIL import Image
from colorama import Style, init


# ASCII settings
ASCII_CHARS = "@%#*+=-:. "
FPS = 10
init(autoreset=True)

# Default size
WIDTH, HEIGHT = shutil.get_terminal_size((160, 80))
HEIGHT -= 6

# Global state
is_paused = False
stop_requested = False
captions = []
show_captions = True
video_start_time = None
current_time = 0
CAPTION_OFFSET = -0.5
video_duration = 999


def rgb_to_ansi(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def frame_to_ascii(img):
    img = img.resize((WIDTH, HEIGHT)).convert("RGB")
    output = ""
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = img.getpixel((x, y))
            brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
            char = ASCII_CHARS[brightness * (len(ASCII_CHARS) - 1) // 255]
            output += rgb_to_ansi(r, g, b) + char + Style.RESET_ALL
        output += "\n"
    return output


def get_stream_url(youtube_url):
    result = subprocess.run(
        ["yt-dlp", "-g", "-f", "best[ext=mp4]", youtube_url],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True)
    return result.stdout.strip()


def get_video_duration(youtube_url):
    result = subprocess.run(["yt-dlp", "--print", "duration", youtube_url],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        h, m, s = map(int, result.stdout.strip().split(":"))
        return h * 3600 + m * 60 + s
    except:
        return 999


def hide_cursor():
    print("\033[?25l", end="")


def show_cursor():
    print("\033[?25h", end="")


def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02}:{s:02}"


def get_current_caption(timestamp):
    for cap in captions:
        if cap["start"] <= timestamp <= cap["end"]:
            return cap["text"]
    return ""


def control_thread():
    global is_paused, stop_requested, show_captions, video_start_time
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while not stop_requested:
            ch = sys.stdin.read(1)
            if ch == 'p':
                is_paused = not is_paused
            elif ch == 'q':
                stop_requested = True
                break
            elif ch == 'c':
                show_captions = not show_captions
            elif ch == 'f':
                video_start_time -= 5
            elif ch == 'b':
                video_start_time += 5
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def find_json_subtitle():
    json_files = glob.glob("*.en.json3")
    return json_files[0] if json_files else None


def download_and_parse_subtitles(youtube_url):
    for f in glob.glob("*.json3"):
        os.remove(f)

    subprocess.run([
        "yt-dlp", "--write-auto-sub", "--sub-lang", "en",
        "--sub-format", "json3", "--skip-download", "-o", "subs", youtube_url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    json_file = find_json_subtitle()
    if not json_file:
        return None

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data.get("events", []):
        start = entry.get("tStartMs", 0) / 1000
        dur = entry.get("dDurationMs", 0) / 1000
        text = ''.join(seg.get("utf8", '') for seg in entry.get("segs", []))
        if text.strip():
            captions.append({
                "start": start + CAPTION_OFFSET,
                "end": start + dur + CAPTION_OFFSET,
                "text": text.strip()
            })

    return json_file
def generate_visualizer_data(audio_stream, height, bars=8):
    data = np.frombuffer(audio_stream.read(1024, exception_on_overflow=False), dtype=np.int16)
    fft_data = np.abs(np.fft.rfft(data))
    fft_data = np.clip(fft_data, 1e-7, None)  # prevent div-by-zero
    bar_heights = np.interp(fft_data[:bars], [0, np.max(fft_data)], [0, height]).astype(int)

    # Build vertical ASCII bars
    visualizer = [''] * height
    for row in range(height):
        for bar in bar_heights:
            visualizer[row] += '█' if height - row <= bar else ' '
    return visualizer


def stream_ascii_raw(video_url):
    global video_start_time, current_time
    print("🎞 Streaming ASCII video (p: pause, q: quit, f: >>, b: <<, c: captions)...")
    hide_cursor()

    ffmpeg_proc = subprocess.Popen([
        "ffmpeg", "-probesize", "100M", "-analyzeduration", "100M",
        "-re", "-i", video_url,
        "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-loglevel", "quiet", "-"
    ], stdout=subprocess.PIPE)

    ffplay_proc = subprocess.Popen([
        "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", video_url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    frame_size = WIDTH * HEIGHT * 3
    threading.Thread(target=control_thread, daemon=True).start()
    video_start_time = time.time()

    try:
        while not stop_requested:
            if is_paused:
                time.sleep(0.1)
                continue

            raw_frame = ffmpeg_proc.stdout.read(frame_size)
            if not raw_frame:
                break

            current_time = time.time() - video_start_time
            img = Image.frombytes("RGB", (WIDTH, HEIGHT), raw_frame)
            print("\033[H", end="")
            print(frame_to_ascii(img))

            caption = get_current_caption(current_time) if show_captions else ""
            progress_len = int((WIDTH - 20) * (current_time / video_duration))
            progress_bar = "[" + "=" * progress_len + ">" + " " * ((WIDTH - 20) - progress_len) + "]"

            print(Style.BRIGHT + caption.center(WIDTH) + Style.RESET_ALL)
            print(f"{format_time(current_time)}".ljust(10) + progress_bar + f"{format_time(video_duration)}".rjust(10))
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        ffmpeg_proc.kill()
        ffplay_proc.kill()
        for f in glob.glob("*.json3"):
            os.remove(f)
        print(Style.RESET_ALL)


def stream_fastfetch_overlay(url):
    global video_start_time, current_time
    print(f"\033[{shutil.get_terminal_size().lines};1H🎞 Streaming in Fastfetch mode (p: pause, q: quit, f: >>, b: <<)...")
    print("\033[2J\033[H", end="")  # Clear screen + move to top-left



    stream_url = get_stream_url(url)
    tmp_frame = "fastfetch_overlay.png"

    # Get fastfetch output once
    try:
        fastfetch_output = subprocess.run(
           ["script", "-q", "-c", "fastfetch --logo none --color blue", "/dev/null"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True
        ).stdout.strip().splitlines()
    except:
        fastfetch_output = []

    ffmpeg_proc = subprocess.Popen([
        "ffmpeg", "-probesize", "100M", "-analyzeduration", "100M",
        "-re", "-i", stream_url,
        "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-loglevel", "quiet", "-"
    ], stdout=subprocess.PIPE)
    # inside stream_fastfetch_overlay(), just below ffmpeg_proc:
    ffplay_proc = subprocess.Popen([
        "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", stream_url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


    frame_size = WIDTH * HEIGHT * 3
    threading.Thread(target=control_thread, daemon=True).start()
    video_start_time = time.time()

    try:
        while not stop_requested:
            if is_paused:
                time.sleep(0.1)
                continue

            raw_frame = ffmpeg_proc.stdout.read(frame_size)
            if not raw_frame:
                break

            current_time = time.time() - video_start_time
            img = Image.frombytes("RGB", (WIDTH, HEIGHT), raw_frame)
            ascii_frame = frame_to_ascii(img).splitlines()

            # Pad both to match height
            max_lines = max(len(ascii_frame), len(fastfetch_output))
            ascii_frame += [' ' * WIDTH] * (max_lines - len(ascii_frame))
            fastfetch_output += [''] * (max_lines - len(fastfetch_output))

            print("\033[H", end="")
            for i in range(max_lines):
                print(f"{ascii_frame[i]}   {fastfetch_output[i]}")
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        ffmpeg_proc.kill()
        ffplay_proc.kill()
        print(Style.RESET_ALL)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--fastfetch-mode", action="store_true", help="Render one frame inline for Fastfetch")
    parser.add_argument("--width", type=int, help="Override ASCII width")
    parser.add_argument("--height", type=int, help="Override ASCII height")
    parser.add_argument("--loop", action="store_true", help="Loop the video playback")
    parser.add_argument("-v", "--visualizer", action="store_true", help="Show vertical audio visualizer")


    args = parser.parse_args()
    url = args.url

    global WIDTH, HEIGHT
    if args.width:
        WIDTH = args.width
    if args.height:
        HEIGHT = args.height - 6

    if args.fastfetch_mode:
        while True:
            stream_fastfetch_overlay(url)
            if not args.loop:
                break
        return

    print("🔗 Getting stream URL...")
    stream_url = get_stream_url(url)

    print("⏳ Getting duration...")
    global video_duration
    video_duration = get_video_duration(url)

    print("💬 Checking for captions...")
    json_file = download_and_parse_subtitles(url)
    if json_file:
        print(f"📄 Captions ready: {json_file}")
    else:
        print("⚠️  No captions found.")

    while True:
        stream_ascii_raw(stream_url)
        if not args.loop:
            break
        print("\n🔁 Replaying...\n")
        time.sleep(1)



if __name__ == "__main__":
    main()
