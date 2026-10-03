#!/usr/bin/env python3
"""Shrink listing photos for the web and make card thumbnails, before uploading to R2.

    python3 scripts/prepare-photos.py <srcDir> <outDir>

Writes, without touching the originals in <srcDir>:
  <outDir>/<name>.jpg          1600px long edge, JPEG q78  -> upload to listings/<id>
  <outDir>/thumbs/<name>.jpg   900px long edge,  JPEG q75  -> upload to thumbs/listings/<id>

Then:
  node scripts/r2-manage.js upload <outDir> listings/<id>
  node scripts/r2-manage.js upload <outDir>/thumbs thumbs/listings/<id>

Cards and the gallery strip load the thumbs/ copy and fall back to the full photo if it is
missing, so skipping the second upload is safe, just heavier.
"""
import os
import sys

from PIL import Image, ImageOps

WEB_EDGE, WEB_Q = 1600, 78
THUMB_EDGE, THUMB_Q = 900, 75


def save(im, edge, quality, path):
    copy = im.copy()
    copy.thumbnail((edge, edge), Image.LANCZOS)
    copy.save(path, 'JPEG', quality=quality, optimize=True, progressive=True)
    return os.path.getsize(path)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    if os.path.abspath(src) == os.path.abspath(out):
        sys.exit('outDir must differ from srcDir (originals are never overwritten).')
    os.makedirs(os.path.join(out, 'thumbs'), exist_ok=True)

    before = after = done = 0
    for name in sorted(os.listdir(src)):
        path = os.path.join(src, name)
        if name.startswith('.') or not os.path.isfile(path):
            continue
        try:
            im = Image.open(path)
            im = ImageOps.exif_transpose(im)  # bake in phone rotation
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGBA')
                bg = Image.new('RGB', im.size, (255, 255, 255))  # transparent areas -> white, not black
                bg.paste(im, mask=im.getchannel('A'))
                im = bg
            im = im.convert('RGB')
        except Exception as e:
            print(f'  skipped {name}: {e} (HEIC? export as JPEG first)')
            continue
        base = os.path.splitext(name)[0] + '.jpg'
        size = save(im, WEB_EDGE, WEB_Q, os.path.join(out, base))
        save(im, THUMB_EDGE, THUMB_Q, os.path.join(out, 'thumbs', base))
        before += os.path.getsize(path)
        after += size
        done += 1
        print(f'  {base}: {os.path.getsize(path) // 1024} KB -> {size // 1024} KB')

    print(f'{done} photo(s): {before / 1048576:.1f} MB -> {after / 1048576:.1f} MB, thumbs in {out}/thumbs')


if __name__ == '__main__':
    main()
