#!/usr/bin/env python3
"""Build native Xcursor files with the selected Vitalux accent."""
from pathlib import Path
import json
import struct
from PIL import Image, ImageDraw
PACKAGE = Path(__file__).resolve().parents[1] / 'package'
COLORS = json.loads((PACKAGE / 'design/vitalux.json').read_text())['colors']
def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)

def cursor():
    folder = (PACKAGE / 'payload') / 'icons/LiquidGlass-Cursors'
    write(folder/'index.theme', '[Icon Theme]\nName=Liquid Glass\nComment=Original high-DPI glass cursors\nInherits=breeze_cursors\n')
    aliases = {
        'default':['left_ptr','arrow','top_left_arrow'], 'pointer':['hand2','pointing_hand','hand','9d800788f1b08800ae810202380a0822'],
        'text':['xterm','ibeam'], 'crosshair':['cross'], 'move':['fleur','all-scroll','size_all'],
        'ew-resize':['size_hor','sb_h_double_arrow','col-resize'], 'ns-resize':['size_ver','sb_v_double_arrow','row-resize'],
        'nwse-resize':['size_fdiag','bd_double_arrow'], 'nesw-resize':['size_bdiag','fd_double_arrow'],
        'not-allowed':['forbidden','crossed_circle','no-drop'], 'grab':['openhand','hand1'], 'grabbing':['closedhand'],
        'wait':['watch'], 'progress':['left_ptr_watch'], 'help':['question_arrow','whats_this'],
        'copy':['dnd-copy'], 'alias':['dnd-link'], 'dnd-move':[]
    }
    for kind, names in aliases.items():
        chunks=[]
        for size in (24,32,48,64,96):
            for frame in range(12 if kind in ('wait','progress') else 1):
                factor=4; im=Image.new('RGBA',(size*factor,size*factor)); d=ImageDraw.Draw(im)
                u=size*factor/32
                def line(points,fill='#17304d',width=2):
                    d.line([(x*u,y*u) for x,y in points],fill=fill,width=max(1,round(width*u)),joint='curve')
                if kind in ('text','crosshair','move','ew-resize','ns-resize','nwse-resize','nesw-resize'):
                    if kind=='text':
                        lines=[[(12,4),(20,4)],[(16,4),(16,28)],[(12,28),(20,28)]]
                    elif kind=='crosshair':lines=[[(16,3),(16,29)],[(3,16),(29,16)]]
                    else:
                        lines=[]
                        if kind in ('move','ew-resize'):lines += [[(4,16),(28,16)],[(9,11),(4,16),(9,21)],[(23,11),(28,16),(23,21)]]
                        if kind in ('move','ns-resize'):lines += [[(16,4),(16,28)],[(11,9),(16,4),(21,9)],[(11,23),(16,28),(21,23)]]
                        if kind=='nwse-resize':lines=[[(6,6),(26,26)],[(6,14),(6,6),(14,6)],[(18,26),(26,26),(26,18)]]
                        if kind=='nesw-resize':lines=[[(6,26),(26,6)],[(6,18),(6,26),(14,26)],[(18,6),(26,6),(26,14)]]
                    for p in lines:line(p,'#ffffff',5);line(p,width=2)
                    hot=(size//2,size//2)
                elif kind=='wait':hot=(size//2,size//2)
                elif kind=='not-allowed':
                    d.ellipse((5*u,5*u,27*u,27*u),fill='#f7fbffe8',outline='#ffffff',width=round(3*u))
                    d.ellipse((6*u,6*u,26*u,26*u),outline='#174b7e',width=round(2*u));line([(9,9),(23,23)],'#174b7e',2)
                    hot=(size//2,size//2)
                elif kind in ('pointer','grab','grabbing'):
                    pts=[(11,15),(11,5),(13,3),(15,5),(15,12),(17,10),(19,12),(21,12),(24,15),(24,22),(20,28),(12,28),(6,19),(7,16),(10,18)]
                    if kind=='grabbing':pts=[(8,13),(11,10),(15,11),(18,10),(23,13),(24,21),(20,28),(12,28),(7,21)]
                    d.polygon([(x*u,y*u) for x,y in pts],fill='#f1f7ff',outline='#ffffff',width=round(3*u))
                    line(pts+[pts[0]],'#253b57',1.3);hot=(round(13/32*size),round(4/32*size))
                else:
                    pts=[(4,2),(4,25),(10,20),(15,30),(19,28),(14,18),(23,18)]
                    d.polygon([(x*u,y*u) for x,y in pts],fill='#253b57',outline='#ffffff',width=round(1.8*u))
                    line([(5.5,5),(5.5,20)],COLORS['secondary'],.65);hot=(round(4/32*size),round(2/32*size))
                if kind in ('wait','progress'):
                    cx,cy,r=(16,16,10) if kind=='wait' else (23,23,7)
                    box=((cx-r)*u,(cy-r)*u,(cx+r)*u,(cy+r)*u)
                    d.arc(box,0,359,fill=COLORS['track'],width=round(3*u))
                    d.arc(box,frame*30,frame*30+235,fill=COLORS['accent'],width=round(3*u))
                if kind in ('help','copy','alias','dnd-move'):
                    d.ellipse((18*u,18*u,31*u,31*u),fill=COLORS['accent'],outline='#ffffff',width=round(u))
                    if kind=='help':line([(23,21),(26,21),(26,23),(24,25)],'#ffffff',1.4);line([(24,28),(24.1,28)],'#ffffff',1.7)
                    elif kind=='copy':line([(21,24),(28,24)],'#ffffff',1.3);line([(24,21),(24,28)],'#ffffff',1.3)
                    else:line([(21,26),(27,21),(27,25)],'#ffffff',1.3)
                im=im.resize((size,size),Image.Resampling.LANCZOS)
                pixels=bytearray()
                for r,g,b,alpha in im.getdata():
                    pixels+=struct.pack('<I',(alpha<<24)|((r*alpha//255)<<16)|((g*alpha//255)<<8)|(b*alpha//255))
                chunk=struct.pack('<9I',36,0xfffd0002,size,1,size,size,*hot,80 if kind in ('wait','progress') else 0)+pixels
                chunks.append((size,chunk))
        pos=16+len(chunks)*12
        toc=[]
        for size,chunk in chunks:toc.append(struct.pack('<3I',0xfffd0002,size,pos));pos+=len(chunk)
        data=struct.pack('<4I',0x72756358,16,0x10000,len(chunks))+b''.join(toc)+b''.join(c for _,c in chunks)
        for name in [kind,*names]:
            dest=folder/'cursors'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)

if __name__ == '__main__':
    cursor()
