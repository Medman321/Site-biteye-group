#!/usr/bin/env python3
"""Appose le cachet rond de SARL BIT EYE sur un PDF de facture ou de devis.

Usage : python3 apposer_cachet.py <entree.pdf> <cachet.png> <sortie.pdf> [--taille 150]

Le cachet est placé dans le cadre « Cachet et signature » du PDF de la plateforme
de facturation (repéré par le mot « Cachet » sur la dernière page qui le contient).
Sans ce cadre, il est placé en bas à droite de la dernière page.
Le fichier du cachet n'est jamais versé dans ce dépôt public : il est dans le Drive
(« Charte et logos » / « Cachet rond SARL BIT EYE.png »).
Dépendances : pypdf, reportlab, Pillow, poppler-utils (pdftotext).
"""
import argparse, io, re, subprocess
from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

p = argparse.ArgumentParser()
p.add_argument('entree'); p.add_argument('cachet'); p.add_argument('sortie')
p.add_argument('--taille', type=float, default=150, help='largeur du cachet en points (150 = 5,3 cm)')
a = p.parse_args()

# Cachet : fond transparent ramené au blanc, recadré sur l'encre
raw = Image.open(a.cachet).convert('RGBA')
im = Image.new('RGB', raw.size, (255, 255, 255)); im.paste(raw, mask=raw.split()[3])
bbox = ImageChops.invert(im.convert('L')).point(lambda v: 255 if v > 40 else 0).getbbox()
im = im.crop(bbox)

reader = PdfReader(a.entree)
n = len(reader.pages)
page_idx, pos = n - 1, None
for i in range(n - 1, -1, -1):
    xml = subprocess.run(['pdftotext', '-f', str(i + 1), '-l', str(i + 1), '-bbox', a.entree, '-'],
                         capture_output=True, text=True).stdout
    m = re.search(r'xMin="([\d.]+)" yMin="[\d.]+" xMax="[\d.]+" yMax="([\d.]+)">Cachet<', xml)
    if m:
        page_idx, pos = i, (float(m.group(1)), float(m.group(2)))
        break

page = reader.pages[page_idx]
pw, ph = float(page.mediabox.width), float(page.mediabox.height)
w = a.taille; h = w * im.size[1] / im.size[0]
if pos:   # centre du cadre : 116 pt à droite du mot « Cachet », 100 pt sous sa ligne
    cx, cy_top = pos[0] + 116, pos[1] + 100
else:
    cx, cy_top = pw - 60 - w / 2, ph - 60 - h / 2
x, y = cx - w / 2, ph - cy_top - h / 2

buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(pw, ph))
c.drawImage(ImageReader(im), x, y, width=w, height=h)
c.save(); buf.seek(0)
page.merge_page(PdfReader(buf).pages[0])
out = PdfWriter()
for pg in reader.pages:
    out.add_page(pg)
out.write(a.sortie)
print(f'cachet posé page {page_idx + 1} ({"cadre trouvé" if pos else "cadre absent, bas de page"}) -> {a.sortie}')
