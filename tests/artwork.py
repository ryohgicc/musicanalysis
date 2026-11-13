"""Original geometric PNGs used only for fictional examples and browser tests."""
import struct
import zlib


def synthetic_png(seed=0):
    size=96
    palettes=[((78,106,221),(223,229,255)),((77,151,141),(221,240,226)),((191,142,104),(252,233,211)),((152,124,181),(237,228,248))]
    ink,paper=palettes[seed%len(palettes)]
    rows=[]
    for y in range(size):
        row=bytearray([0])
        for x in range(size):
            cx,cy=x-48,y-48
            ring=(int((cx*cx+cy*cy)**.5)//7)%2==0
            inside=cx*cx+cy*cy<33**2
            c=ink if ring and inside else paper
            row.extend(c)
        rows.append(bytes(row))
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
