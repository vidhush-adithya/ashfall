#!/usr/bin/env python3
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1920, 1080
wp = Image.open(sys.argv[1]).resize((W, H)).convert("RGBA")
out = sys.argv[2]
F = lambda s, b=False: ImageFont.truetype("DejaVuSansMono-Bold.ttf" if b else "DejaVuSansMono.ttf", s)
C = dict(ash=(12,11,9), soot=(20,18,15), char=(29,26,22), slag=(42,38,32), grit=(74,68,58),
         dust=(110,102,87), bone=(168,159,140), bright=(194,184,163), rust=(139,90,60),
         ochre=(154,131,72), moss=(93,106,72), blood=(122,51,41), steel=(85,98,112))
img = wp.copy()
d = ImageDraw.Draw(img)

def shadow(box, r=24):
    sh = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(sh).rectangle([box[0]-4, box[1]+2, box[2]+4, box[3]+10], fill=(0,0,0,190))
    return sh.filter(ImageFilter.GaussianBlur(r))

# bar
bx0, by0, bx1, by1 = 10, 6, W-10, 34
ov = Image.new("RGBA", (W, H), (0,0,0,0)); od = ImageDraw.Draw(ov)
od.rectangle([bx0,by0,bx1,by1], fill=C['soot']+(235,), outline=C['slag'])
od.rectangle([bx0,by1-1,bx1,by1+1], fill=C['rust'])
img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
f = F(13, True); fr = F(13)
d.rectangle([bx0,by0,bx0+118,by1-2], fill=C['rust']); d.text((bx0+12,by0+6), "☢ ASHFALL", font=f, fill=C['ash'])
x = bx0+128
for name, act in [("RECON",0),("WEB",0),("PWN",1),("REV",0),("INTEL",0)]:
    w = d.textlength(name, font=f)+20
    if act:
        d.rectangle([x,by0+1,x+w,by1-2], fill=C['char']); d.rectangle([x,by1-3,x+w,by1-2], fill=C['ochre'])
    d.text((x+10,by0+6), name, font=f, fill=C['bone'] if act else C['dust'])
    x += w
d.text((x+12,by0+6), "// solve.py — nvim", font=fr, fill=C['dust'])
clk = "23:41  ·  Thu 05 Nov"; d.text(((W-d.textlength(clk,font=f))/2, by0+6), clk, font=f, fill=C['bone'])
right = [("VPN 10.10.14.37",'vpn'),("NET 192.168.1.23",0),("CPU  9%",0),("MEM 31%",0),("47°",0),("VOL 60%",0),("BAT 82%",0),("⏻",'pw')]
x = bx1
for t, k in reversed(right):
    w = d.textlength(t, font=f)+20; x -= w
    if k == 'vpn': d.rectangle([x,by0+1,x+w,by1-2], fill=C['moss'])
    d.line([x,by0+1,x,by1-2], fill=C['slag'])
    d.text((x+10,by0+6), t, font=f, fill=C['ash'] if k=='vpn' else (C['rust'] if k=='pw' else C['dust']))

def window(box, lines, active, title=None, tabs=None):
    global img, d
    img = Image.alpha_composite(img, shadow(box))
    ov = Image.new("RGBA", (W, H), (0,0,0,0)); od = ImageDraw.Draw(ov)
    od.rectangle(box, fill=C['ash']+(240 if active else 225,))
    img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
    col = C['rust'] if active else (36,33,28)
    d.rectangle([box[0]-2,box[1]-2,box[2]+2,box[3]+2], outline=col, width=2)
    y = box[1]+14
    if tabs:
        tx = box[0]+12
        for i,t in enumerate(tabs):
            w = d.textlength(t, font=F(12,True))+16
            if i==0: d.rectangle([tx,y-4,tx+w,y+14], fill=C['rust'])
            d.text((tx+8,y-2), t, font=F(12,True), fill=C['ash'] if i==0 else C['dust']); tx += w+14
        y += 26
    for segs in lines:
        x = box[0]+14
        for txt, c in segs:
            d.text((x,y), txt, font=F(14), fill=C[c] if not active else C[c])
            x += d.textlength(txt, font=F(14))
        y += 21

g = 10; top = 34+g+4
L = (14, top, 14+int((W-28-g)*0.5), H-14)
R1 = (L[2]+g+4, top, W-14, top+int((H-top-14-g)*0.55))
R2 = (L[2]+g+4, R1[3]+g+4, W-14, H-14)

window(L, [
 [("┌─","grit"),("vidhush","rust"),("@ashfall ","dust"),("~/ctf/current ","bone"),("vpn:10.10.14.37","moss")],
 [("└─","grit"),("❯ ","ochre"),("checksec --file=files/chall","bone")],
 [("    Arch:       amd64-64-little","bone")],
 [("    RELRO:      ","bone"),("Partial RELRO","ochre")],
 [("    Stack:      ","bone"),("No canary found","blood")],
 [("    NX:         ","bone"),("NX enabled","moss")],
 [("    PIE:        ","bone"),("No PIE (0x400000)","blood")],
 [("",'bone')],
 [("┌─","grit"),("vidhush","rust"),("@ashfall ","dust"),("~/ctf/current ","bone"),("vpn:10.10.14.37","moss")],
 [("└─","grit"),("❯ ","ochre"),("python3 solve.py REMOTE HOST=10.129.42.7 PORT=31337","bone")],
 [("[+] ","moss"),("Opening connection to 10.129.42.7 on port 31337: Done","bone")],
 [("[*] ","steel"),("leak: puts@libc = 0x7f3a1c280e50","bone")],
 [("[*] ","steel"),("libc base       = 0x7f3a1c200000","bone")],
 [("[*] ","steel"),("Switching to interactive mode","bone")],
 [("$ ","ochre"),("cat flag.txt","bone")],
 [("HTB{4sh_f4lls_0n_th3_st4ck}","ochre")],
 [("$ ","ochre"),("█","ochre")],
], False, tabs=["1:exploit","2:gdb","3:nc"])

window(R1, [
 [("pwndbg> ","rust"),("cyclic -l 0x6161616c","bone")],
 [("Finding cyclic pattern of 8 bytes: b'laaaaaaa' (hex: 0x6c61616161616161)","dust")],
 [("Found at offset ","bone"),("40","ochre")],
 [("pwndbg> ","rust"),("x/6gx $rsp","bone")],
 [("0x7ffd3e1c8a18:  ","steel"),("0x00000000004011c3  0x0000000000404018","bone")],
 [("0x7ffd3e1c8a28:  ","steel"),("0x0000000000401030  0x0000000000401156","bone")],
 [("pwndbg> ","rust"),("rop --grep 'pop rdi'","bone")],
 [("0x00000000004011c3: pop rdi; ret;","moss")],
], True, tabs=["pwndbg"])

window(R2, [
 [("# Ret 2 Wasteland   [pwn]  —  HTB Uni 2026","ochre")],
 [("",'bone')],
 [("## Recon / observations","rust")],
 [("- no canary, no PIE → ret2libc via puts leak","bone")],
 [("- offset 40, pop rdi @ 0x4011c3","bone")],
 [("",'bone')],
 [("## Flag","rust")],
 [("HTB{4sh_f4lls_0n_th3_st4ck}","bone")],
], False, tabs=["notes.md"])

# notification
nb = (W-14-380, top+12, W-14-12, top+12+70)
ov = Image.new("RGBA", (W, H), (0,0,0,0)); od = ImageDraw.Draw(ov)
od.rectangle(nb, fill=C['soot']+(245,), outline=C['ochre'], width=2)
img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img)
d.text((nb[0]+14, nb[1]+12), "flag secured", font=F(14,True), fill=C['bright'])
d.text((nb[0]+14, nb[1]+36), "HTB{4sh_f4lls_0n_th3_st4ck}", font=F(13), fill=C['bone'])
img.convert("RGB").save(out)
print("ok")
