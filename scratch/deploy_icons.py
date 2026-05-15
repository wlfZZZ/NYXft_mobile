import shutil
import os

src = r"C:\Users\bhara\.gemini\antigravity\brain\32d154a8-155a-45a3-a884-1ebe76262a20\nyxft_app_icon_1778777076746.png"
dst_dir = r"c:\Users\bhara\OneDrive\Documents\NYXft\static\img"

if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

shutil.copy(src, os.path.join(dst_dir, "icon-512.png"))
shutil.copy(src, os.path.join(dst_dir, "icon-192.png"))
print("Icons deployed successfully.")
