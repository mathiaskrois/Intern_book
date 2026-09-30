"""Create editable editorial HTML from the fixed, read-only website archive."""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]; BOOK=ROOT/'book'; ARC=ROOT/'website-archive'
INDEX=json.loads((ARC/'index.json').read_text()); RECORDS={r['id']:r for r in INDEX['pages']}
PAGES=[]; SOURCES=[]
E=lambda x:html.escape(str(x),quote=True)

def personalize(text):
    """Recipient-requested adaptation; leave the archival originals untouched."""
    text=text.replace('Mathias Krøis Møller','Anton')
    return re.sub(r'Mathias','Anton',text,flags=re.I)

def personalized_dashboard():
    """Re-render the archived DOM, rather than painting over screenshot pixels."""
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=2)
        page.route('http://**/*',lambda r:r.abort())
        page.route('https://**/*',lambda r:r.abort())
        page.goto((ARC/'pages/dashboard.html').as_uri(),wait_until='load')
        page.evaluate('''()=>{const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode())n.textContent=n.textContent.replace(/Mathias/g,'Anton');document.querySelectorAll('iframe').forEach(e=>e.remove());}''')
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(BOOK/'assets/dashboard-detail.png'),clip={'x':350,'y':80,'width':990,'height':138})
        browser.close()
    return '../assets/dashboard-detail.png'

def lattice():
    names=['house','flash','users','calendar','folder','beer','check','clock','dashboard']
    return '<div class="lattice" aria-hidden="true">'+''.join(f'<span>{icon(n)}</span>' for n in names)+'</div>'

def soup(key): return BeautifulSoup((ARC/RECORDS[key]['content_html_path']).read_text(),'html.parser')
def icon(name,cls=''):return f'<svg class="icon {cls}" viewBox="0 0 24 24"><use href="#i-{name}"/></svg>'
def label(text):return f'<div class="kicker">{E(text)}</div>'
def note(text):return f'<div class="note">{E(text)}</div>'
def page(title,body,keys=(),cls='',section='INTERN'):
    title=personalize(title);body=personalize(body)
    n=len(PAGES)+1
    urls=[RECORDS[k]['url'] for k in keys]
    short=urlsplit(urls[0]).path if urls else 'GAHK · 27.09.2026'
    source=f'<a href="{E(urls[0])}">{E(short)}</a>' if urls else E(short)
    PAGES.append(f'<section class="page {cls}" id="page-{n}" data-title="{E(title)}"><header class="running"><span class="brand">GAHK / INTERN</span><span>{E(section)}</span></header><div class="page-content">{body}</div><footer class="folio"><span class="url">{source}</span><span class="num">{n:02}</span></footer></section>')
    SOURCES.append({'page':n,'title':title,'archive_ids':list(keys),'urls':urls})

def notice(key,compact=False):
    s=soup(key);n=s.select_one('.notice-card');body=n.select_one('.board-body')
    for x in body.select('img'):x.decompose()
    author=n.select_one('.notice-name').get_text(' ',strip=True)
    date=n.select_one('time').get_text(' ',strip=True)
    return f'<article class="notice {"compact" if compact else ""}"><div class="byline">{E(author)}<br>{E(date)}</div><div class="body">{body.decode_contents()}</div></article>'

def table(headers,rows,widths=None,cls=''):
    cols='<colgroup>'+''.join(f'<col style="width:{v}%">' for v in widths)+'</colgroup>' if widths else ''
    return '<table class="table '+cls+'">'+cols+'<thead><tr>'+''.join(f'<th>{E(x)}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'

def crop(key,box,name):
    src=ARC/RECORDS[key]['screenshot_path'];dest=BOOK/'assets'/name
    with Image.open(src) as im:im.crop(box).save(dest)
    return '../assets/'+name

def tree_node(li):
    node=li.find(['a','span'],recursive=False)
    text=node.get_text(' ',strip=True)
    text=re.sub(r"\s+('(?:19|20|21|22|23|24|25|26))$",r' <em>\1</em>',E(text))
    children=li.find('ul',recursive=False)
    sub='<ul>'+''.join(tree_node(x) for x in children.find_all('li',recursive=False))+'</ul>' if children else ''
    return '<li><span class="node">'+text+'</span>'+sub+'</li>'

def branch_containing(name):
    root=soup('stamtree').select_one('.lineage > ul > li > ul')
    for li in root.find_all('li',recursive=False):
        if name in li.get_text():return '<ul class="lineage">'+tree_node(li)+'</ul>'
    raise ValueError(name)

def main():
    (BOOK/'assets').mkdir(exist_ok=True)
    # Three overview crops only. There are no album/archive assets in the book.
    dash=personalized_dashboard()
    album=crop('fotoalbum',(355,83,1327,343),'fotoalbum-overview-detail.png')
    archive=crop('arkiv',(355,80,1327,350),'arkiv-overview-detail.png')
    original=BeautifulSoup((ARC/'pages/dashboard.html').read_text(),'html.parser')
    symbols=''.join(str(x).replace('viewbox=','viewBox=') for x in original.select('symbol'))

    # 01 — cover
    page('INTERN — til Anton',f'<div class="cover-logo">{icon("house")}<span class="edition">G. A. Hagemanns<br>Kollegium</span></div><h1 class="cover-wordmark">INTERN</h1><div class="cover-band"><div class="cover-motto">Et sted<br><em>at høre til.</em></div>{lattice()}</div><div class="cover-bottom"><span>PERSONLIG GAVEUDGAVE<br><strong>TIL ANTON</strong></span><span>09<br>2026</span></div>',cls='cover no-folio')
    # 02
    page('Titel og udgave',label('G. A. Hagemanns Kollegium')+'<h1>Intern</h1><p class="lead">Et øjebliksbillede af et digitalt fællesrum.</p><div class="title-rule"></div><p>Hilsner, opslag, aftaler, værelser og små praktiske beskeder. Denne bog samler et udvalg af GAHK Intern, som siden så ud den 27.&nbsp;september&nbsp;2026.</p><p>Teksterne er hentet fra hjemmesiden. De er sat på ny til papir; udvalgte skærmudsnit viser, hvor de kommer fra.</p><div class="dedication">Til Anton.</div><div class="push"><p class="meta">Personlig gaveudgave · September 2026<br>32 sider · 148 × 210 mm</p></div>',cls='title-page no-folio')
    # 03
    toc=[('01','Oversigt',[('Goddag, Mathias','4'),('Dashboard · Alumnelisten · Min profil','5–7')]),('02','Samtaler',[('Den Hurtige og kanalerne','8–10'),('Opslagstavlen','11–14'),('Begivenheder og kalender','15–16')]),('03','Huset',[('Værelser og værelsestjek','17–18'),('AK-krydser og Ølkælder','19–20'),('Reparationer','21–22')]),('04','Ressourcer',[('Stamtræ og statistik','23–25'),('Fotoalbum og Arkiv — oversigterne','26–27'),('Navigation · Kilder · Kolofon','28–30')])]
    body=label('Et overblik')+'<h1>Indhold</h1>'
    for num,title,rows in toc:
        body+=f'<div class="toc-group"><div class="section-no">{num}</div><div><h2>{title}</h2>'+''.join(f'<div class="toc-row"><span>{a}</span><span>{b}</span></div>' for a,b in rows)+'</div></div>'
    page('Indhold',body+note('Bogen er et redigeret udsnit. Wiki samt billeder og filer inde i Fotoalbum og Arkiv indgår ikke.'),section='Indhold')
    # 04
    body=label('01 / Oversigt')+'<div class="wide-rule"></div><h1 class="display">Goddag,<br><em>Mathias</em></h1><div class="gap"></div><p class="lead">G. A. Hagemanns Kollegium</p><div class="push">'
    for item,value in [('Aktiv måned','2026-09'),('Dine roller','indstilling')]:body+=f'<div class="kv"><dt>{item}</dt><dd>{value}</dd></div>'
    body+='</div><div class="source-note">Dashboardets hilsen, personligt tilpasset denne gaveudgave.</div>'
    page('Goddag, Mathias',body,['dashboard'],section='Oversigt',cls='tint')
    # 05
    body=label('Oversigt / Dashboard')+'<h1>En indgang<br>til hverdagen</h1>'+f'<img class="facsimile" src="{dash}" alt="Udsnit af dashboardets hilsen og aktive måned"><div class="caption">Dashboardets øverste felt · Navnet er tilpasset Anton.</div><div class="gap"></div><h2>Genveje</h2>'
    shortcuts=[('users','Alumneliste'),('check','Mine AK-krydser'),('beer','Min ølkælder-saldo'),('folder','Ansøgninger')]
    body+='<div class="navigation-list">'+''.join(f'<div class="navigation-item">{icon(i)}<span>{t}</span></div>' for i,t in shortcuts)+'</div><div class="push panel warm"><div class="label">Begivenheder på GAHK</div><p class="lead" style="margin:3mm 0 0">Åbn i Google →</p></div>'+note('Her vises dashboardets labels og genveje. Adgangsoplysninger og den eksterne kalender er udeladt.')
    page('Dashboard',body,['dashboard'],section='Oversigt')
    # 06
    rows=RECORDS['alumneliste']['tables'][0][1:]
    selected=[]
    for row in rows[:12]:
        name=re.sub(r'^[A-ZÆØÅ]{2,3}\n','',row[0]);name=re.sub(r'[\n🧓👑✎]','',name).strip()
        selected.append([E(name),E(row[1])])
    body=label('Oversigt / Alumnelisten')+'<h1>Navne i huset</h1><p class="lead">September 2026</p><p class="meta">Udsnit: de første 12 navne i listens alfabetiske visning.</p>'+table(['Navn','Værelse'],selected,[85,15],'roster')
    body+=note('Alumnelisten har 61 rækker i den aktuelle måned. Siden viser også embedsgruppe, rengøring, fylgje, fødselsdag, indflytning, studie og kontaktfelter.')
    page('Alumnelisten',body,['alumneliste'],section='Oversigt')
    # 07
    s=soup('beboer-456-profil');name=s.h1.get_text(' ',strip=True);study=s.select_one('.page-head p').get_text(' ',strip=True)
    values=[(x.select_one('.l').get_text(' ',strip=True),x.select_one('.r').get_text(' ',strip=True)) for x in s.select('.kv')]
    body=label('Oversigt / Min profil')+'<div class="roundel">A</div>'+f'<h1 class="profile-name">{E(name)}</h1><p class="small sans">{E(study)}</p><dl class="profile-grid">'
    for k,v in values:
        if k in ['Værelse','Embedsgruppe','Rengøring','Fylgje','Indflyttet']:body+=f'<div class="kv"><dt>{E(k)}</dt><dd>{E(v)}</dd></div>'
    body+='</dl><div class="push"><h3>Seneste opslag</h3><p>Ingen opslag endnu.</p></div>'+note('Profilnavnet er tilpasset Anton. De øvrige felter viser kildeprofilens oplysninger, ikke modtagerens. Kontaktfelter er udeladt.')
    page('Min profil',body,['beboer-456-profil'],section='Oversigt')
    # 08
    body=label('02 / Samtaler')+icon('flash','big')+'<div class="gap"></div><h1>Den Hurtige</h1><div class="push"><div class="pull-mark">“</div><blockquote class="quote">Flyttekasser<br><em>any 1?</em></blockquote><div class="source-note">Niels Christian Jakobsen<br>Den Hurtige · 16:31</div></div><div class="gap"></div><div class="gap"></div>'
    page('Den Hurtige',body,['den-hurtige','den-hurtige-178-traad'],section='Samtaler',cls='tint')
    # 09
    s=soup('den-hurtige');body=label('Den Hurtige / Udsnit')+'<h1>Små beskeder</h1>'
    for mid in [177,180,181,182,187]:
        msg=s.select_one(f'#msg-{mid}');author=msg.select_one('.msg-name').get_text(' ',strip=True);txt=msg.select_one('.msg-text').get_text(' ',strip=True);tm=msg.select_one('.msg-time').get_text(' ',strip=True)
        body+=f'<div class="chat-item"><div class="chat-who"><span>{E(author)}</span><time>{E(tm)}</time></div><p>{E(txt)}</p></div>'
    body+=note('Fem beskeder fra den synlige strøm. Klokkeslæt er sidens egne; udløbstællere og reaktionsknapper er udeladt.')
    page('Små beskeder',body,['den-hurtige'],section='Samtaler')
    # 10
    body=label('Den Hurtige / Kanaler')+'<h1>Fem rum<br>i samme strøm</h1><div class="channels">'
    for name,status in [('Den Hurtige','13 synlige beskeder'),('TV-Rezz','1 synlig besked'),('G. A. Sportsmann','Ingen beskeder lige nu.'),('GAHKroom','Ingen beskeder lige nu.'),('M.H.G.A','Ingen beskeder lige nu.')]:body+=f'<div class="channel"><h3>{name}</h3><div class="meta">{status}</div></div>'
    body+='</div><h3>Sidens egen forklaring</h3><p>Skriv noget der er relevant den næste times tid — fælles kaffe, en pakke i porten, hjælp til at bære. Beskeder forsvinder fra feedet når tiden er gået, men de bliver ikke slettet: de ligger i arkivet, som du trækker ned til fra toppen. Skal noget stå fast, hører det stadig hjemme i ankebogen eller på opslagstavlen.</p>'+note('Kanalnavne og tilstand ved arkiveringen. Forklaringen er gengivet fra en tom kanal.')
    page('Kanaler',body,['den-hurtige-sportsmann','den-hurtige-tv-rezz','den-hurtige-gahkroom','den-hurtige-mhga'],section='Samtaler')
    # 11
    body=label('Kollegiet / Opslagstavlen')+'<h1>Opslagstavlen</h1><div class="push"><div class="pull-mark">“</div><blockquote class="quote">Jeg ved ikke,<br>hvad en<br><em>Markdown</em> er</blockquote><div class="source-note">Carl Andersen · 18. september 2026<br>Uddrag. Hele opslaget følger på næste side.</div></div><div class="gap"></div><div class="gap"></div>'
    page('Opslagstavlen',body,['opslagstavle','opslagstavle-8'],section='Samtaler',cls='tint')
    # 12
    body=label('Opslagstavlen / Praktisk')+'<h1>Carls Håndbog</h1>'+notice('opslagstavle-8')+'<div class="push panel warm"><h3>Velkommen til Opslagstavlen</h3><p class="small">I kan bare prøve at lave et opslag og slette det efter</p><p class="small">Man kan også indsætte billeder</p><div class="meta">Anton Mosquera Storgaard · 26. august 2026<br>Opslagets tekst. Billedet er udeladt.</div></div>'
    page('Carls Håndbog',body,['opslagstavle-8','opslagstavle-1'],section='Samtaler')
    # 13
    body=label('Opslagstavlen / Begivenhed')+'<h1>Årets vigtigste<br>billede</h1><div class="letter">'+notice('opslagstavle-11',True)+'</div>'+note('Personlig gaveversion af opslaget: navnet er tilpasset Anton. Det vedhæftede billede er udeladt.')
    page('Årets vigtigste billede',body,['opslagstavle-11'],section='Samtaler')
    # 14
    body=label('Opslagstavlen / Andet')+'<h1>KEN’s mange<br>kvaliteter</h1>'+notice('opslagstavle-7',True)
    body+='<div class="comment-stack"><p>bruger jeg den her rigtigt?!</p><div class="meta">Wilma Riemer Eis · 14. Sept 2026, 21:01</div><div style="height:3mm"></div><p>Ja det er perfekt :))</p><div class="meta">Anton Mosquera Storgaard · 14. Sept 2026, 21:20</div><div style="height:3mm"></div><p>Hyggeligt!</p><div class="meta">Anton Claes Pallavicini · 14. Sept 2026, 22:38</div></div>'
    page('KEN’s mange kvaliteter',body,['opslagstavle-7'],section='Samtaler')
    # 15
    s=soup('begivenheder-4');body=label('Kollegiet / Begivenheder')+'<div class="event-banner"><span class="event-day">21</span><div><div class="label">Oktober 2026</div><p class="meta">onsdag · 19.00–20.30<br>Spisesalen</p></div></div><h1 style="font-size:36px">Første fællesmøde<br>i den nye periode!!</h1>'
    body+='<div class="event-copy">'+E(s.select_one('.event-description').get_text('\n',strip=True))+'</div><div class="push"><div class="kv"><dt>Arrangør</dt><dd>Anton Claes Pallavicini</dd></div><div class="kv"><dt>Kommer du?</dt><dd>4 kommer</dd></div></div>'+note('Begivenhedens oplysninger og tekst ved arkiveringen. Tilmeldingstallet er et øjebliksbillede.')
    page('Begivenheder',body,['begivenheder-4'],section='Samtaler')
    # 16
    s=soup('begivenheder-kalender');body=label('Begivenheder / Kalender')+'<h1>September 2026</h1><div class="calendar">'+''.join(f'<div class="day-head">{x}</div>' for x in ['man','tir','ons','tor','fre','lør','søn'])
    for c in s.select('.cal-cell'):
        cls='outside' if 'is-outside' in c.get('class',[]) else 'today' if 'is-today' in c.get('class',[]) else ''
        body+=f'<div class="cell {cls}"><span class="day">{c.select_one(".cal-daynum").text}</span>'
        for b in c.select('.cal-birthday-name'):body+=f'<span class="birthday">{E(b.text)}</span>'
        for ev in c.select('.cal-event'):body+=f'<span class="event {"cancelled" if "is-cancelled" in ev.get("class",[]) else ""}">{E(ev.get_text(" ",strip=True))}</span>'
        body+='</div>'
    body+='</div><div class="cols"><div><h3>GF!!!</h3><p class="small">Der er GF wooohoo</p><div class="meta">24. september · Festsalen<br>20 kommer</div></div><div><h3>Test</h3><p class="small">Begivenheden er aflyst.</p><div class="meta">5. september · 308</div></div></div>'+note('Kalenderruden er sat på ny efter sidens septembervisning. Fødselsdagsnavne, den aflyste begivenhed og nabomånedens dage er bevaret.')
    page('Kalender',body,['begivenheder-kalender','begivenheder-2','begivenheder-1'],section='Samtaler')
    # 17
    body=label('03 / Huset')+'<h1>Søg værelse</h1><p class="lead">Din kvotient</p><p>Kvotienten (K) afgør rækkefølgen når værelser fordeles — højest vinder.</p><div class="equation"><span><i>K</i> = </span><span class="frac"><span><i>a</i> · 100</span><span><i>a</i> + <i>b</i> + 12</span></span></div><div class="formula-def"><span class="letter-a">a</span><p>antal måneder du har boet på GAHK (minus orlov)</p></div><div class="formula-def"><span class="letter-a">b</span><p>antal måneder til du er færdig med studiet</p></div><p class="meta">Begge regnet frem til Oktober 2026.</p><div class="push panel warm"><p style="margin:0">Der er ingen værelser i udbud lige nu, men du kan altid se din kvotient her.</p></div>'+note('Formlen og forklaringen er fra siden. Definitionerne er typografisk opdelt; der er ikke beregnet en ny kvotient.')
    page('Søg værelse',body,['soegvaerelse'],section='Huset',cls='tint')
    # 18
    body=label('Værelser / Værelsestjek')+'<h1>Et hus i fem plan</h1><p class="meta">Værelsesoversigt · sat på ny fra siden.</p>'
    roomrows=RECORDS['vaerelsestjek']['tables'][0][1:]
    for floor in ['stuen','1. sal','2. sal','3. sal','4. sal']:
        numbers=[r[0] for r in roomrows if r[1].split(' · ')[0]==floor]
        body+='<div class="room-floor"><div class="label">'+E(floor)+'</div><div class="room-numbers">'+''.join('<span>'+E(n)+'</span>' for n in numbers)+'</div></div>'
    body+='<div class="gap"></div><h3>Værelse 101 · et udsnit af tjekket</h3><p class="meta">Tjekket 2025-07-06 09:14 af Magnus Guldberg Pedersen.</p>'
    body+=table(['Kriterie','Score','Kommentar'],[['Loft','2 (1–5)','Lidt revner / bulet maling'],['Skabe inventar','1 (0–1)','Ingen skohylde'],['Vask armatur','2 (0–2)','armatur drypper']],[35,20,45])
    body+=note('Etage- og værelsesnumre fra oversigten. Herunder tre rækker fra et værelsestjek; skalaerne er sidens egne.')
    page('Værelsestjek',body,['vaerelsestjek','vaerelsestjek-se-101'],section='Huset')
    # 19
    rows=RECORDS['ak']['tables'][0][1:]
    body=label('Grupper & konti / AK-krydser')+'<h1>Dine<br>aktivitetskrydser</h1><div class="saldo"><div><div class="label">Saldo</div><div class="number">−2</div></div><div class="meta">målet er at holde sig<br>på 0 eller derover</div></div>'
    rendered=[]
    for r in rows:rendered.append([E(r[0]),f'<span class="change">{E(r[1])}</span>',E(r[3])])
    body+=table(['Dato','±','Note'],rendered,[24,9,67],'ledger')+note('Hele den viste posteringstabel, med noterne ordret. Kolonnen »Type« er udeladt. Saldoen tilhører den indloggede visning.')
    page('AK-krydser',body,['ak'],section='Huset')
    # 20
    rows=RECORDS['oelkaelder-min-saldo']['tables'][0][1:11]
    body=label('Grupper & konti / Ølkælder')+'<h1>Min ølkælder-<br>saldo</h1><div class="saldo"><div class="number">−312,33</div><div class="label">kr.</div></div><h3>Kontoudtog · de 10 seneste linjer</h3>'
    body+=table(['Dato','Tekst','Beløb'],[[E(r[0][5:10]),E(r[1]),E(r[2])] for r in rows],[15,62,23],'ledger')+note('Udsnit af kontoens septemberposteringer. Datoer er forkortet til måned–dag; alle linjer er fra 2026. Bankoplysninger er udeladt.')
    page('Ølkælder',body,['oelkaelder-min-saldo'],section='Huset')
    # 21
    s=soup('reparationer');body=label('Værktøjer / Reparationer')+'<h1>Det skal<br>lige fikses</h1><div class="status-grid">'
    for col in s.select('.kanban-col'):
        spans=col.select('.kanban-col-head > span');body+=f'<div class="status-tile"><div class="number">{E(spans[1].text)}</div><div class="meta">{E(spans[0].text)}</div></div>'
    body+='</div>'
    for tid in ['4','6']:
        c=s.select_one(f'[data-task-id="{tid}"]');ps=c.find_all('p',recursive=False)
        body+=f'<div class="repair-card"><h3>{E(c.h3.get_text(" ",strip=True))}</h3><p class="meta">{E(ps[0].get_text(" ",strip=True))}</p><p>{E(ps[1].get_text(" ",strip=True))}</p><div class="meta">{E(ps[-1].get_text(" ",strip=True))}</div></div>'
    body+=note('Statuskolonnernes antal og to udvalgte fejlmeldinger, som de stod ved arkiveringen.')
    page('Reparationer',body,['reparationer','reparationer-4','reparationer-6'],section='Huset')
    # 22
    s=soup('reparationer-3');body=label('Reparationer / Papirautomat')+'<h1>En fejlmelding<br>og fire noter</h1><p class="meta">Varme Køkken · Meldt af Adam Sjøqvist<br>12. Sept 2026, 13:18</p><p>Sidder løst på væggen og mangler dæksel. Gør den meget besværlig at bruge. Har været i stykker i lang tid.</p><hr class="rule">'
    for c in s.select('.board-list > div'):
        ps=c.find_all('p',recursive=False);body+=f'<div class="conversation-item"><p>{E(ps[0].get_text(" ",strip=True))}</p><div class="meta">{E(ps[1].get_text(" ",strip=True))}</div></div>'
    page('Papirautomat',body,['reparationer-3'],section='Huset')
    # 23
    body=label('04 / Ressourcer')+'<h1>GAHK’s<br>Stamtræ</h1><p class="lead">Alumnernes fylgje-slægt - hvem der er fylgje for hvem, med rod i «Hagemanns Ånd».</p><div class="gap"></div><div class="lineage-root">Hagemanns Ånd</div>'+branch_containing('Mathias Krøis Møller')+note('En hel gren fra sidens rod. Forbindelser og årstal følger originalen; navnet er tilpasset Anton som i resten af gaveudgaven. Dette er et udsnit.')
    page('Stamtræ',body,['stamtree'],section='Ressourcer',cls='tint')
    # 24
    body=label('Stamtræ / Flere grene')+'<h1>Fylgje for<br>hinanden</h1>'
    for name in ['Karen Visby Østergaard','Carl Kjølby','Anton Mosquera Storgaard']:body+='<div class="branch">'+branch_containing(name)+'</div>'
    body+=note('Tre yderligere grene fra Hagemanns Ånd. Siden indeholder flere grene end de viste. De små årstal er gengivet som på hjemmesiden.')
    page('Fylgje for hinanden',body,['stamtree'],section='Ressourcer')
    # 25
    rows=RECORDS['statistik']['tables'][0]
    body=label('Ressourcer / Statistik')+'<h1>Rundvisninger<br>pr. universitet</h1><p class="lead">2026</p><div style="margin:5mm 0">'
    for name,count in rows:body+=f'<div class="bar-row"><span>{E(name)}</span><span class="bar" style="width:{100*int(count)/123:.3f}%"></span><span class="count">{count}</span></div>'
    body+='</div>'+note('Samtlige rækker fra sidens universitetstabel, tegnet som søjler. Kildens forskellige stavemåder er bevaret og ikke slået sammen. Statistik-siden viser også ansøgningstyper, henvisninger og besøg pr. dag.')
    page('Statistik',body,['statistik'],section='Ressourcer')
    # 26
    s=soup('fotoalbum');body=label('GAHKs fælles minder')+'<h1>Fotoalbum</h1>'+f'<img class="facsimile" src="{album}" alt="Øverste del af fotoalbumoversigten, uden albumfotos"><div class="caption">Skærmudsnit af oversigten. Albumindhold indgår ikke.</div><div class="gap"></div><h3>Et udvalg af oversigtens titler</h3><div class="album-list">'
    wanted=['Fotofernisering','GAHK i snevejr - Februar 05','Hectors romantiske gåtur med tøserne!!',"TDC - Oktober 2004/Niels' ørefetich",'Vores smukke kollegium (ml) 2003','Blandet halløj som folk lægger udenfor mappe','Fest hmmm','Haveprojekt']
    for name in wanted:
        card=next(x for x in s.select('.album-card') if x.select_one('.album-card-name').text.strip()==name)
        year=card.find_parent('section',class_='album-folder').h2.get_text(' ',strip=True)
        count=card.select_one('.album-card-count').text.strip()
        body+=f'<div><div class="album-name">{E(name)}</div><div class="album-year">{year} · {count}</div></div>'
    body+='</div>'+note('Kun selve oversigten er repræsenteret. Ingen af de billeder eller videoer, som albumtitlerne henviser til, er med i bogen.')
    page('Fotoalbum — oversigten',body,['fotoalbum'],section='Ressourcer')
    # 27
    body=label('Ressourcer / Arkiv')+'<h1>Arkiv</h1><p class="lead">Tre indgange.</p><div class="gap"></div>'+''.join(f'<div class="folder-row">{icon("folder")}<span>{name}</span></div>' for name in ['Billeder','Fælles dokumenter','Indstillingen'])
    body+=f'<div class="push"><img class="facsimile" src="{archive}" alt="Arkivets oversigt med tre mapper"><div class="caption">Skærmudsnit · Arkivets startside.</div></div>'+note('Sidens mappenavne er gengivet. Ingen mapper er foldet ud i bogen, og ingen lagrede filer eller billeder er med.')
    page('Arkiv — oversigten',body,['arkiv'],section='Ressourcer')
    # 28
    groups=[('Oversigt',['Dashboard','Min profil','Den Hurtige','Opslagstavle','Begivenheder','Alumneliste','Fotoalbum']),('Værelser',['Søg værelse','Værelsestjek','Værelsesudbud']),('Grupper & konti',['AK-krydser','Ølkælder']),('Værktøjer',['Reparationer']),('Administration',['Ansøgninger','Rediger indhold']),('Ressourcer',['Stamtræ','Statistik','Arkiv','Fejl & ønsker'])]
    body=label('Navigation / Et kort over siden')+'<h1>Fra menuen</h1><div class="cols">'
    for part in [groups[:3],groups[3:]]:
        body+='<div>'
        for name,items in part:body+=f'<div class="map-group"><h3>{name}</h3><p>'+ '<br>'.join(items)+'</p></div>'
        body+='</div>'
    body+='</div>'+note('Menuens grupper og navne. Værelsesudbud, Ansøgninger og Rediger indhold er kun med som menupunkter. Wiki er udeladt. Fejl & ønsker fører til projektets eksterne fejlrapportering.')
    page('Navigation',body,['dashboard'],section='Register')
    # 29
    source_groups=[('4–5','Dashboard','/intern/'),('6','Alumnelisten','/intern/alumneliste/'),('7','Min profil','/intern/beboer/456/profil'),('8–10','Den Hurtige og kanalerne','/intern/den-hurtige/'),('11–14','Opslagstavlen · opslag 1, 7, 8 og 11','/intern/opslagstavle/'),('15','Fællesmøde · nr. 4','/intern/begivenheder/4'),('16','Kalender · begivenhed 1 og 2','/intern/begivenheder/kalender'),('17','Søg værelse','/intern/soegvaerelse/'),('18','Værelsestjek · oversigt og værelse 101','/intern/vaerelsestjek/'),('19','Dine aktivitetskrydser','/intern/ak/'),('20','Min ølkælder-saldo','/intern/oelkaelder/min-saldo'),('21–22','Reparationer · Papirautomat','/intern/reparationer/'),('23–24','GAHK’s Stamtræ','/intern/stamtree/'),('25','Statistik','/intern/statistik/'),('26','Fotoalbum · oversigt','/intern/fotoalbum/'),('27','Arkiv · oversigt','/intern/arkiv/'),('28','Navigation','/intern/'),('31','Papirautomat · Adams sidste note','/intern/reparationer/3')]
    body=label('Register / Kilder')+'<h1>Tilbage til siden</h1><p class="meta">Alle stier hører til www.gahk.dk.<br>De kræver adgang til den interne hjemmeside.</p><div class="sources">'
    for pp,title,path in source_groups:body+=f'<div class="source-row"><span class="source-pages">{pp}</span><div>{E(title)}<br><a class="path" href="https://www.gahk.dk{E(path)}">{E(path)}</a></div></div>'
    body+='</div>'
    page('Kilder',body,section='Register')
    # 30
    body=label('Om denne udgave')+'<h1>Kolofon</h1><div class="colophon"><h3>Et øjebliksbillede</h3><p>GAHK Intern, arkiveret med tilladelse den 27. september 2026. Bogen er et udvalg af hjemmesidens hovedområder.</p><h3>Til Anton</h3><p>Denne personlige gaveudgave tilpasser navnet til Anton i hilsner, tekst, profil, stamtræ og dashboardudsnit. Profilfelter, saldi og relationer følger kildevisningen; de er ikke oplysninger om modtageren.</p><h3>Tekst og billeder</h3><p>Opslag og noter tilhører deres afsendere. Ud over navnetilpasningen er ordlyden bevaret. Bogens overskrifter og redaktionelle noter er tilføjet. Uddrag er markeret.</p><p>Wiki er udeladt. Fotoalbum og Arkiv vises kun som oversigter, uden lagrede fotos og filer. Skærmudsnittet af dashboardet er gengivet med det tilpassede navn.</p><h3>Fra skærm til papir</h3><p>EB Garamond og Manrope, indlejret fra lokale filer under SIL Open Font License. Grøn, creme og messing fra hjemmesiden; et grafisk mønster af dens egne ikoner.</p><h3>Personlig gaveudgave · 02</h3><p>148 × 210 mm · 32 sider<br>Til Anton · September 2026</p><p class="meta">Adgangsoplysninger og kontaktfelter er ikke trykt. Skiftende oplysninger gælder arkiveringstidspunktet.</p></div>'
    page('Kolofon',body,section='Kolofon')
    # 31
    body=label('En sidste note')+'<div class="push"><div class="pull-mark">“</div><blockquote class="quote">Hey selv tak.<br><em>Hav’ det<br>smukt.</em></blockquote><div class="source-note">Adam Sjøqvist<br>Papirautomat · 17. Sept 2026, 20:04</div></div><div class="gap"></div><div class="gap"></div>'
    # Preserve the original straight apostrophe in the source text, even in display typography.
    body=body.replace('Hav’','Hav&#x27;')
    page('Hav det smukt',body,['reparationer-3'],cls='farewell tint',section='En sidste note')
    # 32
    body=f'<div class="cover-logo">{icon("house")}<span class="edition">GAHK / INTERN</span></div><div class="back-initial">A</div><div class="back-dedication">Til <em>Anton.</em></div><div class="cover-rule"></div><p style="margin-top:6mm;color:#d9dfd3">Et udsnit af hjemmesiden.<br>Et øjeblik bevaret på papir.</p><div class="cover-bottom"><span>PERSONLIG GAVEUDGAVE · 02</span><span>09 / 2026</span></div>'
    page('Bagside',body,cls='cover back no-folio')
    assert len(PAGES)==32
    document='<!doctype html><html lang="da"><head><meta charset="utf-8"><title>INTERN — til Anton</title><link rel="stylesheet" href="book.css"><link rel="stylesheet" href="edition.css"></head><body><svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute">'+symbols+'</svg>'+''.join(PAGES)+'</body></html>'
    (BOOK/'src/book.html').write_text(document)
    (BOOK/'src/page-manifest.json').write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2))
    print('Built 32 editable A5 pages from archived sources.')

if __name__=='__main__':main()
