"""Render sequential A5, audit geometry/fonts, then impose a separate A4 booklet."""
import json
import re
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageOps, ImageDraw
from playwright.sync_api import sync_playwright

BOOK=Path(__file__).resolve().parent
MM=72/25.4
OUT=BOOK/'output'; QA=BOOK/'qa'

def main():
    OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1000,'height':1200},device_scale_factor=1)
        requests=[]; errors=[]
        page.on('requestfailed',lambda r:errors.append({'url':r.url,'failure':r.failure}))
        page.route('http://**/*',lambda r:r.abort());page.route('https://**/*',lambda r:r.abort())
        page.goto((BOOK/'src/book.html').as_uri(),wait_until='networkidle')
        page.emulate_media(media='print')
        page.evaluate('''async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));}''')
        audit=page.evaluate('''()=>({
          fonts:[...document.fonts].map(f=>({family:f.family,status:f.status})),
          missingImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),
          missingIcons:[...document.querySelectorAll('use')].map(u=>u.getAttribute('href')).filter(id=>!document.querySelector(id)),
          localOverflow:[...document.querySelectorAll('.calendar .cell,.channel,td')].filter(e=>e.scrollHeight>e.clientHeight+1||e.scrollWidth>e.clientWidth+1).map(e=>({page:e.closest('.page').id,text:e.innerText})),
          pages:[...document.querySelectorAll('.page')].map((p,i)=>{const c=p.querySelector('.page-content'),b=c.getBoundingClientRect();
            const bad=[...c.querySelectorAll('*')].filter(e=>!e.closest('svg')).map(e=>({tag:e.tagName,text:e.innerText?.slice(0,90),r:e.getBoundingClientRect()})).filter(x=>x.r.width>0&&x.r.height>0&&(x.r.bottom>b.bottom+1||x.r.right>b.right+1||x.r.left<b.left-1));
            return {page:i+1,title:p.dataset.title,scrollHeight:c.scrollHeight,clientHeight:c.clientHeight,overflow:bad.map(x=>({tag:x.tag,text:x.text,bottom:x.r.bottom-b.bottom,right:x.r.right-b.right}))};})
        })''')
        audit['request_failures']=errors
        (QA/'layout-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
        page.pdf(path=str(OUT/'book-a5-draft.pdf'),width='148mm',height='210mm',print_background=True,prefer_css_page_size=True,display_header_footer=False,tagged=True)
        browser.close()
    src=fitz.open(OUT/'book-a5-draft.pdf')
    assert len(src)==32 and len(src)%4==0
    # Chromium rounds paper dimensions to device pixels; normalize the page boxes
    # to exact ISO trim dimensions without rasterizing or shrinking the content.
    for leaf in src:
        leaf.set_mediabox(fitz.Rect(0,0,148*MM,210*MM))
    src.set_metadata({'title':'INTERN — til Anton · G. A. Hagemanns Kollegium','author':'GAHK · privat gaveudgave','subject':'Et udsnit af GAHK Intern, 27. september 2026','creator':'Editable HTML/CSS · Chromium · PyMuPDF'})
    src.set_toc([[1,'Oversigt',4],[1,'Samtaler',8],[2,'Opslagstavlen',11],[2,'Begivenheder',15],[1,'Huset',17],[2,'Reparationer',21],[1,'Ressourcer',23],[2,'Fotoalbum og Arkiv — oversigter',26],[1,'Kilder og kolofon',29]])
    src.save(OUT/'book-a5.pdf',garbage=4,deflate=True)
    src.close();src=fitz.open(OUT/'book-a5.pdf')
    fonts={}; pagechecks=[]
    for n,p in enumerate(src):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False)
        pix.save(QA/f'page-{n+1:02}.png')
        for font in p.get_fonts(full=True):
            xref=font[0]; info=src.extract_font(xref);embedded=len(info[3]);embedding='font file'
            if font[2]=='Type3':
                # Chromium embeds color emoji as self-contained Type 3 glyph programs.
                procs=src.xref_get_key(xref,'CharProcs')[1]
                embedded=sum(len(src.xref_stream(int(n)) or b'') for n in re.findall(r'(\d+) 0 R',procs))
                embedding='embedded glyph programs (emoji)'
            fonts[str(xref)]={'name':font[3] or 'Color emoji','type':font[2],'embedded_bytes':embedded,'embedding':embedding}
        dims=[round(p.rect.width/MM,3),round(p.rect.height/MM,3)]
        assert abs(dims[0]-148)<.001 and abs(dims[1]-210)<.001
        blocks=p.get_text('dict')['blocks'];outside=[];sizes=[]
        for b in blocks:
            for line in b.get('lines',[]):
                for s in line['spans']:
                    sizes.append(s['size']);r=fitz.Rect(s['bbox'])
                    if r.x0<8*MM or r.y0<8*MM or r.x1>p.rect.width-8*MM or r.y1>p.rect.height-8*MM:outside.append(s['text'])
        images=[]
        for img in p.get_image_info():
            r=fitz.Rect(img['bbox'])
            if r.width and r.height:images.append({'width':img['width'],'height':img['height'],'ppi_x':round(img['width']/(r.width/72)),'ppi_y':round(img['height']/(r.height/72))})
        pagechecks.append({'page':n+1,'mm':dims,'characters':len(p.get_text()),'minimum_font_pt':round(min(sizes),2) if sizes else None,'outside_8mm_safe_area':outside,'images':images})
    # Four large thumbnails per contact sheet; full-resolution page PNGs are also retained.
    for start in range(0,len(src),4):
        sheet=Image.new('RGB',(1144,1660),'#d8dad3');draw=ImageDraw.Draw(sheet)
        for j in range(4):
            if start+j>=len(src):break
            im=Image.open(QA/f'page-{start+j+1:02}.png').convert('RGB');im.thumbnail((550,781))
            x=14+(j%2)*572;y=27+(j//2)*830
            sheet.paste(im,(x,y));draw.text((x,y-17),f'PAGE {start+j+1:02}',fill='black')
        sheet.save(QA/f'contact-{start//4+1:02}.jpg',quality=95)
    # Single nested booklet: sheet 1 front = [32,1], back = [2,31], etc.
    imposed=fitz.open();ordering=[];n=len(src)
    for i in range(n//4):
        for side,pair in [('front',[n-1-2*i,2*i]),('back',[2*i+1,n-2-2*i])]:
            spread=imposed.new_page(width=297*MM,height=210*MM)
            for slot,source in enumerate(pair):
                # Finished A5 is 148 mm. Center each leaf in an A4 half (148.5 mm).
                x=(slot*148.5+.25)*MM
                spread.show_pdf_page(fitz.Rect(x,0,x+148*MM,210*MM),src,source,keep_proportion=True)
            ordering.append({'sheet':i+1,'side':side,'left':pair[0]+1,'right':pair[1]+1})
    assert sorted(x for r in ordering for x in [r['left'],r['right']])==list(range(1,n+1))
    imposed.set_metadata({'title':'INTERN — til Anton · A4 booklet, short-edge duplex','creator':'PyMuPDF · vector page imposition'})
    imposed.save(OUT/'book-a4-booklet.pdf',garbage=4,deflate=True);imposed.close()
    imposed=fitz.open(OUT/'book-a4-booklet.pdf')
    for i in [0,1,15]:
        imposed[i].get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(QA/f'booklet-side-{i+1:02}.png')
    imposed.close()
    (QA/'imposition.json').write_text(json.dumps(ordering,indent=2))
    (QA/'pdf-audit.json').write_text(json.dumps({'page_count':len(src),'fonts':fonts,'pages':pagechecks,'imposition':ordering},ensure_ascii=False,indent=2))
    src.close()
    (OUT/'book-a5-draft.pdf').unlink(missing_ok=True)
    print(json.dumps({'pages':len(pagechecks),'overflow_pages':[x['page'] for x in audit['pages'] if x['overflow'] or x['scrollHeight']>x['clientHeight']+1],
        'missing_images':audit['missingImages'],'missing_icons':audit['missingIcons'],'local_overflow':audit['localOverflow'],'fonts':audit['fonts'],'unembedded_fonts':[f for f in fonts.values() if not f['embedded_bytes']],
        'unsafe_pages':[x['page'] for x in pagechecks if x['outside_8mm_safe_area']]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
