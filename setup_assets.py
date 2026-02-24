import os
import subprocess
import sys

def create_dummy_assets():
    assets_dir = r"C:\NEXUS\ASSETS"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"Created directory: {assets_dir}")

    ffmpeg_exe = r"C:\NEXUS\ffmpeg.exe"
    
    # 1. Dummy ATF Logo (Red box)
    cmd_logo_atf = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "color=c=red:s=200x100",
        "-frames:v", "1",
        os.path.join(assets_dir, "atf_logo.png")
    ]
    
    # 2. Dummy CanbusFix Logo (Blue box)
    cmd_logo_cbf = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=200x100",
        "-frames:v", "1",
        os.path.join(assets_dir, "canbusfix_logo.png")
    ]
    
    # 3. Dummy Intro (Black 3s)
    cmd_intro = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=3",
        "-c:v", "libx264",
        os.path.join(assets_dir, "intro_community.mp4")
    ]
    
    # 4. Dummy Outro (White 3s)
    cmd_outro = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "color=c=white:s=1280x720:d=3",
        "-c:v", "libx264",
        os.path.join(assets_dir, "outro_subscribe.mp4")
    ]

    commands = [cmd_logo_atf, cmd_logo_cbf, cmd_intro, cmd_outro]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Generated: {cmd[-1]}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating {cmd[-1]}: {e}")

if __name__ == "__main__":
    create_dummy_assets()
