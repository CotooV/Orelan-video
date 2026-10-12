"""Hoja de contactos: python3 tools/contact.py out.png img1 img2 ... [--cols N] [--w PX]"""
import sys
from PIL import Image, ImageDraw
args = sys.argv[1:]
cols, tw = 5, 270
if "--cols" in args:
    i = args.index("--cols"); cols = int(args[i + 1]); del args[i:i + 2]
if "--w" in args:
    i = args.index("--w"); tw = int(args[i + 1]); del args[i:i + 2]
out, files = args[0], args[1:]
ims = [Image.open(f).convert("RGB") for f in files]
th = int(tw * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw + (cols - 1) * 4, rows * (th + 18)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for k, (im, f) in enumerate(zip(ims, files)):
    x, y = (k % cols) * (tw + 4), (k // cols) * (th + 18)
    sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y + 18))
    d.text((x + 3, y + 3), f.split("/")[-1], fill=(220, 220, 220))
sheet.save(out)
