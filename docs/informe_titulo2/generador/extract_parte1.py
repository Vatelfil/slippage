import zipfile, re, json, sys
from lxml import etree
SRC = r"D:\claude agente\TÍTULO I_ Coordinación de Agentes para la Mitigación del _Slippage_.docx"
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ns={'w':W,'r':R}
def q(t): return '{%s}%s'%(W,t)
z=zipfile.ZipFile(SRC)
doc=etree.fromstring(z.read('word/document.xml'))
rels=etree.fromstring(z.read('word/_rels/document.xml.rels'))
relmap={r.get('Id'):r.get('Target') for r in rels}
styles=etree.fromstring(z.read('word/styles.xml'))
sname={}
for s in styles.findall('w:style',ns):
    n=s.find('w:name',ns)
    sname[s.get(q('styleId'))]=n.get(q('val')) if n is not None else s.get(q('styleId'))
numx=etree.fromstring(z.read('word/numbering.xml'))
# numId -> (abstract fmt for level)
abstract={}
for a in numx.findall('w:abstractNum',ns):
    lv={}
    for l in a.findall('w:lvl',ns):
        fmt=l.find('w:numFmt',ns)
        lv[int(l.get(q('ilvl')))]=fmt.get(q('val')) if fmt is not None else 'bullet'
    abstract[a.get(q('abstractNumId'))]=lv
numfmt={}
for n in numx.findall('w:num',ns):
    aid=n.find('w:abstractNumId',ns).get(q('val'))
    numfmt[n.get(q('numId'))]=abstract.get(aid,{})

def runs_of(p):
    out=[]
    def run_obj(r,link=None):
        rpr=r.find('w:rPr',ns)
        b=i=u=False; va=None
        if rpr is not None:
            b = rpr.find('w:b',ns) is not None and rpr.find('w:b',ns).get(q('val')) not in ('0','false')
            i = rpr.find('w:i',ns) is not None and rpr.find('w:i',ns).get(q('val')) not in ('0','false')
            u = rpr.find('w:u',ns) is not None and rpr.find('w:u',ns).get(q('val')) not in ('none',)
            v = rpr.find('w:vertAlign',ns)
            va = v.get(q('val')) if v is not None else None
        txt=''
        extra=None
        for ch in r:
            if ch.tag==q('t'): txt+=ch.text or ''
            elif ch.tag==q('tab'): txt+='\t'
            elif ch.tag==q('br'):
                if ch.get(q('type'))=='page': extra='pagebreak'
                else: txt+='\n'
            elif ch.tag==q('drawing'): extra='drawing'
        o={'t':txt}
        if b:o['b']=1
        if i:o['i']=1
        if u:o['u']=1
        if va:o['va']=va
        if link:o['link']=link
        if extra:o['x']=extra
        return o
    for ch in p:
        if ch.tag==q('r'):
            o=run_obj(ch)
            if o['t'] or o.get('x'): out.append(o)
        elif ch.tag==q('hyperlink'):
            rid=ch.get('{%s}id'%R)
            url=relmap.get(rid) if rid else None
            anchor=ch.get(q('anchor'))
            for r in ch.findall('w:r',ns):
                o=run_obj(r, url or ('#'+anchor if anchor else None))
                if o['t'] or o.get('x'): out.append(o)
    return out

def para(p):
    ps=p.find('w:pPr',ns)
    st='normal'; num=None; jc=None; ind=None
    if ps is not None:
        s=ps.find('w:pStyle',ns)
        if s is not None: st=sname.get(s.get(q('val')),s.get(q('val')))
        npr=ps.find('w:numPr',ns)
        if npr is not None:
            nid=npr.find('w:numId',ns); il=npr.find('w:ilvl',ns)
            if nid is not None and nid.get(q('val'))!='0':
                lvl=int(il.get(q('val'))) if il is not None else 0
                fmt=numfmt.get(nid.get(q('val')),{}).get(lvl,'bullet')
                num={'id':nid.get(q('val')),'lvl':lvl,'fmt':fmt}
        j=ps.find('w:jc',ns)
        jc=j.get(q('val')) if j is not None else None
    return {'k':'p','style':st,'num':num,'jc':jc,'runs':runs_of(p)}

def table(t):
    rows=[]
    for tr in t.findall('w:tr',ns):
        cells=[]
        for tc in tr.findall('w:tc',ns):
            ps=[para(p) for p in tc.findall('w:p',ns)]
            cells.append(ps)
        rows.append(cells)
    return {'k':'tbl','rows':rows}

body=doc.find('w:body',ns)
blocks=[]
for ch in body:
    if ch.tag==q('p'): blocks.append(para(ch))
    elif ch.tag==q('tbl'): blocks.append(table(ch))
json.dump(blocks,open('parte1.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(blocks),'bloques')
# outline
for idx,b in enumerate(blocks[:70]):
    if b['k']=='p':
        t=''.join(r['t'] for r in b['runs'])
        flag=''.join(['D' if r.get('x')=='drawing' else '' for r in b['runs']])+('PB' if any(r.get('x')=='pagebreak' for r in b['runs']) else '')
        print(idx,b['style'], 'LIST' if b['num'] else '', flag, repr(t[:70]))
    else: print(idx,'TABLE',len(b['rows']),'x',len(b['rows'][0]))
