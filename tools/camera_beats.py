import re, cairosvg, sys
s = open('scene_neighbourhood_night.svg').read()
tok = dict(re.findall(r'(--[a-z-]+):\s*(#[0-9A-Fa-f]{6});', s))
cls = dict(re.findall(r'\.(\w+)\s*\{\s*fill:\s*var\((--[a-z-]+)\)', s))
out = s
for c,t in cls.items(): out = out.replace(f'class="{c}"', f'fill="{tok[t]}"')
out = out.replace('class="ln soft"', f'fill="none" stroke="{tok["--irx-line-soft"]}" stroke-linecap="round" stroke-linejoin="round"')
out = out.replace('class="ln"', f'fill="none" stroke="{tok["--irx-line"]}" stroke-linecap="round" stroke-linejoin="round"')
out = re.sub(r'var\((--[a-z-]+)\)', lambda m: tok.get(m.group(1),'#000'), out)

def shot(name, cx, cy, fw, aspect=390/844, px=360):
    fh = fw/aspect
    v = out.replace('viewBox="0 0 2200 900"', f'viewBox="{cx-fw/2:.0f} {cy-fh/2:.0f} {fw:.0f} {fh:.0f}"')
    v = v.replace('width="2200" height="900"', f'width="{fw:.0f}" height="{fh:.0f}"')
    open(f'_{name}.svg','w').write(v)
    cairosvg.svg2png(url=f'_{name}.svg', write_to=f'{name}.png', output_width=px)

# candidate t=0 framings, all 416x900 full-bleed
for i,cx in enumerate((820, 1000, 1150)):
    shot(f'cand{i}', cx, 450, 416)
print('done')