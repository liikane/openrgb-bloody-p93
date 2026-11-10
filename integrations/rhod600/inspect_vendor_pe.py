#!/usr/bin/env python3
"""Read-only PE import and string audit; never executes vendor binaries or accesses HID."""
import hashlib, re, struct, sys
from pathlib import Path
MATCH=re.compile(r"hid|setupapi|usb|winusb|feature|report|writefile|createfile|readfile|device|rgb|backlight|light|shinetek|1a2c|8000|keyboard|firmware|macro|mode|profile",re.I)
def inspect(path):
    b=path.read_bytes()
    assert b[:2]==b"MZ"
    pe=struct.unpack_from("<I",b,0x3c)[0]
    assert b[pe:pe+4]==b"PE\x00\x00"
    machine,n,_,_,_,opt_len,_=struct.unpack_from("<HHIIIHH",b,pe+4)
    opt=pe+24
    pe32=struct.unpack_from("<H",b,opt)[0]==0x10b
    dd=opt+(96 if pe32 else 112)
    sections=[]
    for i in range(n):
        s=opt+opt_len+40*i
        virt,addr,size,off=struct.unpack_from("<IIII",b,s+8)
        sections.append((addr,max(virt,size),off,size))
    def foff(rva):
        for addr,vsize,offset,rawsize in sections:
            if addr<=rva<addr+vsize and rva-addr<rawsize:return offset+rva-addr
        return rva if rva<len(b) else -1
    def cstr(off):
        if off<0 or off>=len(b):return ""
        end=b.find(b"\0",off,min(len(b),off+500))
        return b[off:end].decode("latin1","replace") if end>=0 else ""
    rva,size=struct.unpack_from("<II",b,dd+8)
    print("FILE",path.name,"BYTES",len(b),"SHA256",hashlib.sha256(b).hexdigest().upper(),"MACHINE",hex(machine))
    print("IMPORT TABLE")
    pos=foff(rva)
    for i in range(120):
        if pos<0 or pos+20>len(b):break
        oft,_,_,name,ft=struct.unpack_from("<IIIII",b,pos)
        if not (oft or name or ft):break
        dll=cstr(foff(name)); funcs=[]
        offset=foff(oft or ft)
        width=4 if pe32 else 8
        fmt="<I" if pe32 else "<Q"
        flag=1<<(width*8-1)
        for j in range(500):
            if offset<0 or offset+width>len(b):break
            val=struct.unpack_from(fmt,b,offset)[0]
            if not val:break
            if not (val&flag):
                fname=cstr(foff(val)+2)
                if MATCH.search(fname):funcs.append(fname)
            offset+=width
        print(" ",dll,"HID/USB-related:",",".join(funcs))
        pos+=20
    print("FILTERED STRINGS")
    found=set()
    for m in re.finditer(rb"[\x20-\x7e]{7,}",b):
        value=m.group().decode("ascii")
        if MATCH.search(value) and value not in found and len(found)<60:
            found.add(value)
            print(" ",hex(m.start()),value[:140])
for arg in sys.argv[1:]:
    try:inspect(Path(arg))
    except Exception as e:print(type(e).__name__,str(e))
