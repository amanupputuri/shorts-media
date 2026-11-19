import subprocess, os, colorsys
def mix(h,t,a):
    h=h.lstrip('#'); c=[int(h[i:i+2],16) for i in (0,2,4)]; t=[255,255,255] if t=='w' else [0,0,0]
    return '#%02x%02x%02x'%tuple(int(c[i]+(t[i]-c[i])*a) for i in range(3))
DK='#3a2414'
def eyes(x1,x2,y,r=11):
    return f'<circle cx="{x1}" cy="{y}" r="{r}" fill="{DK}"/><circle cx="{x2}" cy="{y}" r="{r}" fill="{DK}"/><circle cx="{x1+4}" cy="{y-4}" r="4" fill="#fff"/><circle cx="{x2+4}" cy="{y-4}" r="4" fill="#fff"/>'
def smile(x,y,w=18): return f'<path d="M{x-w} {y} Q{x} {y+w} {x+w} {y}" stroke="{DK}" stroke-width="6" fill="none" stroke-linecap="round"/>'
def blush(x1,x2,y): return f'<ellipse cx="{x1}" cy="{y}" rx="13" ry="8" fill="#ff7a8a" opacity=".55"/><ellipse cx="{x2}" cy="{y}" rx="13" ry="8" fill="#ff7a8a" opacity=".55"/>'
G='url(#g)'; G2='url(#g2)'
S={}
S['lion']=lambda:''.join(f'<circle cx="{128+78*__import__("math").cos(a*0.5236):.0f}" cy="{132+78*__import__("math").sin(a*0.5236):.0f}" r="34" fill="{G2}"/>' for a in range(12))+f'<circle cx="128" cy="132" r="72" fill="{G}"/>'+eyes(102,154,120)+f'<ellipse cx="128" cy="150" rx="13" ry="9" fill="{DK}"/>'+smile(128,160,14)+blush(92,164,150)
S['cat']=lambda:f'<path d="M58 120 L70 40 L118 82 Z" fill="{G}"/><path d="M198 120 L186 40 L138 82 Z" fill="{G}"/><ellipse cx="128" cy="140" rx="86" ry="76" fill="{G}"/>'+eyes(98,158,130)+f'<path d="M120 152 L136 152 L128 162 Z" fill="{DK}"/>'+''.join(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{DK}" stroke-width="4" stroke-linecap="round"/>' for x,y,x2,y2 in [(70,160,30,152),(70,170,30,176),(186,160,226,152),(186,170,226,176)])+blush(84,172,165)
S['fox']=lambda:f'<path d="M40 70 L70 20 L110 70 Z" fill="{G2}"/><path d="M216 70 L186 20 L146 70 Z" fill="{G2}"/><path d="M36 70 Q128 40 220 70 Q200 170 128 226 Q56 170 36 70Z" fill="{G}"/><path d="M80 150 Q128 140 176 150 Q160 200 128 226 Q96 200 80 150Z" fill="#fff" opacity=".85"/>'+eyes(96,160,118)+f'<circle cx="128" cy="196" r="12" fill="{DK}"/>'
S['bear']=lambda:f'<circle cx="62" cy="66" r="34" fill="{G}"/><circle cx="194" cy="66" r="34" fill="{G}"/><circle cx="128" cy="138" r="90" fill="{G}"/><ellipse cx="128" cy="168" rx="40" ry="30" fill="#fff" opacity=".6"/>'+eyes(96,160,124)+f'<ellipse cx="128" cy="156" rx="14" ry="10" fill="{DK}"/>'+smile(128,170,12)
S['fish']=lambda:f'<path d="M180 128 L240 70 L232 128 L240 186 Z" fill="{G2}"/><ellipse cx="116" cy="128" rx="96" ry="70" fill="{G}"/><path d="M110 60 Q140 30 160 70Z" fill="{G2}"/>'+f'<circle cx="70" cy="112" r="16" fill="#fff"/><circle cx="66" cy="112" r="9" fill="{DK}"/>'+f'<path d="M30 145 Q42 152 54 145" stroke="{DK}" stroke-width="5" fill="none"/>'
S['star']=lambda:f'<path d="M128 18 L160 92 L238 98 L178 150 L196 228 L128 186 L60 228 L78 150 L18 98 L96 92Z" fill="{G}" stroke-linejoin="round"/>'+eyes(106,150,130,9)+smile(128,156,12)
S['heart']=lambda:f'<path d="M128 220 C40 160 20 110 40 72 C64 28 116 38 128 80 C140 38 192 28 216 72 C236 110 216 160 128 220Z" fill="{G}"/>'+eyes(100,156,120,10)+smile(128,148,14)
S['apple']=lambda:f'<path d="M128 70 C70 40 26 90 34 150 C42 210 92 236 128 214 C164 236 214 210 222 150 C230 90 186 40 128 70Z" fill="{G}"/><rect x="122" y="22" width="12" height="46" rx="6" fill="{DK}"/><path d="M134 46 Q180 20 196 50 Q160 70 134 46Z" fill="#5cc85c"/>'
S['pumpkin']=lambda:f'<ellipse cx="72" cy="146" rx="54" ry="76" fill="{G2}"/><ellipse cx="184" cy="146" rx="54" ry="76" fill="{G2}"/><ellipse cx="128" cy="146" rx="60" ry="82" fill="{G}"/><rect x="118" y="38" width="20" height="36" rx="6" fill="#5b8a2e"/>'
S['ball']=lambda:f'<circle cx="128" cy="128" r="104" fill="{G}"/><path d="M24 128 H232 M128 24 V232 M58 52 Q110 128 58 204 M198 52 Q146 128 198 204" stroke="{DK}" stroke-width="7" fill="none" opacity=".75"/>'
S['flower']=lambda:''.join(f'<ellipse cx="128" cy="70" rx="38" ry="56" fill="{G}" transform="rotate({a} 128 128)"/>' for a in range(0,360,60))+'<circle cx="128" cy="128" r="40" fill="#fff3b0"/>'+eyes(114,142,124,7)
S['bird']=lambda:f'<circle cx="124" cy="136" r="88" fill="{G}"/><path d="M200 130 L246 146 L200 160Z" fill="#ffb02e"/><path d="M60 140 Q100 200 150 160 Q100 150 60 140Z" fill="{G2}"/><path d="M110 50 Q118 20 134 48Z" fill="{G2}"/>'+f'<circle cx="160" cy="112" r="13" fill="{DK}"/><circle cx="164" cy="108" r="5" fill="#fff"/>'
S['mushroom']=lambda:f'<rect x="96" y="120" width="64" height="100" rx="28" fill="#fff3e0"/><path d="M20 140 Q20 30 128 30 Q236 30 236 140Z" fill="{G}"/>'+''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity=".9"/>' for x,y,r in [(80,90,16),(140,64,12),(186,100,18),(120,116,10)])+eyes(112,144,170,8)
S['balloon']=lambda:f'<path d="M128 196 Q124 220 136 244" stroke="{DK}" stroke-width="4" fill="none"/><ellipse cx="128" cy="104" rx="76" ry="90" fill="{G}"/><path d="M118 192 L138 192 L128 204Z" fill="{G2}"/>'
S['moon']=lambda:f'<path d="M170 30 A100 100 0 1 0 226 170 A80 80 0 1 1 170 30Z" fill="{G}"/>'+f'<circle cx="104" cy="120" r="9" fill="{DK}"/>'+smile(112,150,12)
S['bell']=lambda:f'<path d="M128 26 C70 26 60 90 56 150 L36 190 H220 L200 150 C196 90 186 26 128 26Z" fill="{G}"/><circle cx="128" cy="206" r="22" fill="{G2}"/><circle cx="128" cy="22" r="12" fill="{G2}"/>'
S['owl']=lambda:f'<path d="M48 60 L80 40 L96 70Z M208 60 L176 40 L160 70Z" fill="{G2}"/><ellipse cx="128" cy="140" rx="86" ry="92" fill="{G}"/><circle cx="96" cy="112" r="30" fill="#fff"/><circle cx="160" cy="112" r="30" fill="#fff"/>'+eyes(96,160,112,13)+'<path d="M118 140 L138 140 L128 158Z" fill="#ffb02e"/>'
NAMES=list(S)
def svg(name,col):
    lt,dk=mix(col,'w',.55),mix(col,'k',.32)
    defs=f'<defs><radialGradient id="g" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="{lt}"/><stop offset=".45" stop-color="{col}"/><stop offset="1" stop-color="{dk}"/></radialGradient><radialGradient id="g2" cx=".38" cy=".32" r=".8"><stop offset="0" stop-color="{mix(col,"k",.05)}"/><stop offset="1" stop-color="{mix(col,"k",.45)}"/></radialGradient><filter id="s"><feDropShadow dx="0" dy="6" stdDeviation="6" flood-opacity=".28"/></filter></defs>'
    body=S[name](); hl='<ellipse cx="96" cy="70" rx="34" ry="16" fill="#fff" opacity=".35" transform="rotate(-25 96 70)"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">{defs}<g filter="url(#s)">{body}</g>{hl}</svg>'
def render(name,col,out):
    open('/tmp/i.svg','w').write(svg(name,col)); subprocess.run(['rsvg-convert','-w','256','-h','256','/tmp/i.svg','-o',out],check=True)
if __name__=='__main__':
    from PIL import Image
    os.makedirs('lib',exist_ok=True); sh=Image.new('RGB',(256*8,256*2),'white')
    for k,n in enumerate(NAMES):
        render(n,'#ff8a1f',f'lib/{n}.png'); sh.paste(Image.open(f'lib/{n}.png'),((k%8)*256,(k//8)*256),Image.open(f'lib/{n}.png'))
    sh.resize((1024,256)).save('lib_sheet.jpg'); print(len(NAMES))
