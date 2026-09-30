"""Final checks of the rendered deliverables, source fidelity and scope."""
import hashlib
import json
import re
import sys
from pathlib import Path
import pymupdf as fitz
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1];BOOK=ROOT/'book';ARC=ROOT/'website-archive'
sys.path.insert(0,str(ROOT/'crawler'))
from common import credentials
from build import personalize

def norm(text):return re.sub(r'\s+',' ',text).strip()

def main():
    layout=json.loads((BOOK/'qa/layout-audit.json').read_text())
    audit=json.loads((BOOK/'qa/pdf-audit.json').read_text())
    manifest=json.loads((BOOK/'src/page-manifest.json').read_text())
    index=json.loads((ARC/'index.json').read_text())
    assert not layout['missingImages'] and not layout['missingIcons'] and not layout['localOverflow'] and not layout['request_failures']
    assert all(not p['overflow'] and p['scrollHeight']<=p['clientHeight']+1 for p in layout['pages'])
    assert all(f['embedded_bytes']>0 for f in audit['fonts'].values())
    assert all(p['mm']==[148.0,210.0] and not p['outside_8mm_safe_area'] and p['minimum_font_pt']>=7.5 for p in audit['pages'])
    assert len(index['pages'])==58 and not index['failures']
    for r in index['pages']:
        for key in ['content_path','content_html_path','html_path','screenshot_path','main_screenshot_path']:
            assert (ARC/r[key]).is_file(),f'Missing archive file for {r["id"]}'
    for item in manifest:
        assert not any('wiki' in k or (k.startswith(('fotoalbum-','arkiv-'))) for k in item['archive_ids'])
    source=BeautifulSoup((BOOK/'src/book.html').read_text(),'html.parser')
    assert len(source.select('.page'))==32
    assert not re.search('mathias', source.get_text(), re.I)
    assert not re.search('mathias', json.dumps(manifest), re.I)
    assert {Path(i['src']).name for i in source.select('img')}=={'dashboard-detail.png','fotoalbum-overview-detail.png','arkiv-overview-detail.png'}
    for page_no,key in [(12,'opslagstavle-8'),(13,'opslagstavle-11'),(14,'opslagstavle-7')]:
        original=BeautifulSoup((ARC/'pages'/f'{key}.content.html').read_text(),'html.parser').select_one('.board-body')
        for im in original.select('img'):im.decompose()
        typeset=source.select_one(f'#page-{page_no} .notice .body')
        assert norm(personalize(original.get_text(' ',strip=True)))==norm(typeset.get_text(' ',strip=True)),f'Notice text changed on {page_no}'
    a5=fitz.open(BOOK/'output/book-a5.pdf');a4=fitz.open(BOOK/'output/book-a4-booklet.pdf')
    assert len(a5)==32 and len(a4)==16
    for i,p in enumerate(a5):
        assert len(p.get_text().strip())>30
        assert not re.search('mathias',p.get_text(),re.I)
        if 2<=i<31:assert p.get_text().strip().endswith(f'{i+1:02}'),f'Folio mismatch on {i+1}'
    for i,item in enumerate(audit['imposition']):
        p=a4[i]
        assert abs(p.rect.width*25.4/72-297)<.001 and abs(p.rect.height*25.4/72-210)<.001
        for slot,field in enumerate(['left','right']):
            rect=fitz.Rect(slot*p.rect.width/2,0,(slot+1)*p.rect.width/2,p.rect.height)
            actual=norm(p.get_text(clip=rect));expected=norm(a5[item[field]-1].get_text())
            assert actual==expected,f'Imposed text differs: PDF side {i+1}, {field}'
    secret=credentials()['WEBSITE_PASSWORD']
    checked=0
    for base in [BOOK,ARC,ROOT/'crawler']:
        for p in base.rglob('*'):
            if p.suffix in ('.html','.css','.json','.txt','.md','.py','.ics'):
                assert secret not in p.read_text(), 'Credential guard failed'
                checked+=1
    for doc in [a5,a4]:assert secret not in ''.join(p.get_text() for p in doc)
    result={'status':'passed','a5_pages':32,'a4_sides':16,'sheets':8,'source_notice_checks':3,
        'imposed_leaf_checks':32,'credential_files_checked':checked,'archive_pages':58,'successful_assets':sum('path' in a for a in index['assets'].values()),
        'missing_source_assets':sum('error' in a for a in index['assets'].values()),'calendar_downloads':len(index['downloads']),
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BOOK/'output').glob('*.pdf')}}
    (BOOK/'qa/final-verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
