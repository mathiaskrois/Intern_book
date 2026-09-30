"""Repair extraction, finish calendar downloads and audit the final scoped archive."""
import hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from common import ROOT, credentials, launch, authenticate

out=ROOT/'website-archive'; index=json.loads((out/'index.json').read_text())
remove={'alumneliste-naeste-maaned','begivenheder-kalender-abonnement'}
for record in index['pages']:
    if record['id'] in remove:
        for k in ['html_path','content_path','content_html_path','screenshot_path','main_screenshot_path']:
            (out/record[k]).unlink(missing_ok=True)
        index['excluded'][record['url']]='Editing view or personal calendar credential: excluded from final archive'
index['pages']=[r for r in index['pages'] if r['id'] not in remove]
for record in index['pages']:
    s=BeautifulSoup((out/record['html_path']).read_text(),'html.parser')
    c=s.select_one('main')
    for e in c.select('input,textarea,select,button,.emoji-picker,.who-picker,[hidden],script'): e.decompose()
    text='\n'.join(t.strip() for t in c.get_text('\n').splitlines() if t.strip())
    (out/record['content_path']).write_text(text)
    (out/record['content_html_path']).write_text(str(c))
    record['text_sha256']=hashlib.sha256(text.encode()).hexdigest()
index['downloads']=index.get('downloads',[])
for file in (out/'assets').glob('begivenhed-*.ics'):
    event=file.stem.split('-')[-1]
    url=f'https://www.gahk.dk/intern/begivenheder/{event}/ics'
    if not any(d['url']==url for d in index['downloads']):
        index['downloads'].append({'url':url,'path':'assets/'+file.name,'type':'text/calendar'})
with sync_playwright() as p:
    ctx=launch(p); page=ctx.pages[0]; authenticate(page,credentials())
    for error in list(index['failures']):
        if error['url'].endswith('/ics'):
            r=ctx.request.get(error['url'])
            if r.ok:
                event=error['url'].split('/')[-2]; dest='assets/begivenhed-'+event+'.ics'
                (out/dest).write_bytes(r.body())
                if not any(d['url']==error['url'] for d in index['downloads']):
                    index['downloads'].append({'url':error['url'],'path':dest,'type':'text/calendar'})
                index['failures'].remove(error)
    ctx.close()
# Credential URL patterns must not exist in the shareable archive.
secret_url=re.compile(r'https?://[^\s"<>]+/kalender/[A-Za-z0-9_-]{20,}\.ics')
index=json.loads(secret_url.sub('[personal calendar URL redacted]',json.dumps(index,ensure_ascii=False)))
(out/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))
for path in out.rglob('*'):
    if path.suffix in ('.html','.txt','.json','.ics'):
        data=path.read_text()
        assert not secret_url.search(data), 'Personal calendar URL requires redaction'
(out/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2))

counts=Counter(r['section'] for r in index['pages'])
groups=defaultdict(list)
for r in index['pages']:groups[r['text_sha256']].append(r['id'])
exact=[v for v in groups.values() if len(v)>1]
report='''# Website archive report

Captured 27 September 2026 using the supplied account and a persistent Chromium profile.
This is a bounded snapshot of GAHK Intern, revised to match the user's explicit scope:
the wiki is excluded; Fotoalbum and Arkiv are represented only by their overview pages.
No photos or documents stored inside those two sections were archived or used in the book.

'''
report+=f"## Capture totals\n\n- {len(index['pages'])} unique HTML pages.\n- {len(index['assets'])} distinct page asset URLs (images and CSS).\n- {len(index['downloads'])} event calendar downloads.\n- {len(index['failures'])} unresolved page failures.\n- Limit: 100 pages and 3 pagination pages; the queue was exhausted before the limit.\n\n"
report+='## Hierarchy and coverage\n\n'
for k,n in counts.items(): report+=f'- `{k}`: {n} page(s).\n'
report+='''
Each indexed page has its original URL, title, section, discovery parent, outgoing links,
image metadata, cleaned text, passive rendered HTML, full-page screenshot and main-content
screenshot. The root sections are seeded deliberately, so their `parent` is null.
Subpages record the page from which they were discovered. Assets use readable path-derived filenames.

## Scope and manual attention

- **Wiki:** excluded by the user. It was noticed during the initial navigation survey; no wiki material is in the final archive or book.
- **Fotoalbum:** overview captured. It lists 129 albums and 5,990 media entries, counted from the overview. Individual album pages and their photos are deliberately excluded.
- **Arkiv:** overview captured, including the visible folder labels Billeder, Fælles dokumenter and Indstillingen. Their contents are deliberately excluded.
- **Directory and rooms:** current directory overview, the account owner's profile, room overview and one representative read-only room check (101). Other individual records were not expanded; this book represents the interface rather than reproducing every record.
- **Den Hurtige:** five channels and visible message threads captured. Historical/infinite-scroll messages were not expanded; relative expiry times belong to the capture moment, not print time.
- **External Google calendar:** its embed is unavailable in the snapshot; internal event and calendar pages were captured instead. No external website was crawled. The unavailable widget is not reproduced as live calendar information in the book.
- **Credentials:** dashboard access-information panels are redacted before HTML, text and screenshots are saved. Hidden tokens, scripts and live form actions are removed. The personal calendar subscription page and directory editing view are excluded from the final archive.
- **Administrative navigation:** application-management and content-editing destinations are represented only as navigation labels. No applications, edits, registrations, messages, reactions or account changes were submitted.
- **Downloads:** the three event `.ics` endpoints initially caused browser download-navigation errors. They were subsequently saved through authenticated GET requests and are no longer failures.
- **Offline HTML:** local image and stylesheet links are rewritten. Scripts and active forms are disabled; original outgoing URLs are retained in the index. Interactive charts remain faithfully recorded in screenshots, rather than being reconstructed by disabled JavaScript.
- **Missing source asset:** `/media/quick_posts/2026/09/IMG_5052.jpg` returns HTTP 404. Its parent page and surrounding text were captured. The missing image is not used in the book. Of the 38 distinct asset URLs, 37 downloaded successfully.

## Interesting details

- The site greets the logged-in resident with “Goddag, Mathias”.
- “Den Hurtige” has TV-Rezz, G. A. Sportsmann, GAHKroom and M.H.G.A channels.
- The notice board preserves the residents' own spelling and humor, including the Markdown complaint and the planned GAHK group photograph.
- The family tree is rooted in “Hagemanns Ånd”; its nested HTML preserves the actual fylgje relationships.
- Practical vocabulary gives the site its character: AK-krydser, Ølkælder, Varme Køkken, KEN, fylgje and the room-allocation quotient.
- The photo overview contains distinctive titles such as “Blandet halløj som folk lægger udenfor mappe” and “TDC - Oktober 2004/Niels' ørefetich”. These are overview labels, not included album contents.

## Assets and visual identity

Dark and mid greens, warm cream, brass accents, fine borders, small line icons, an uppercase
GAHK/INTERN wordmark and compact navigation. Most body/UI text uses Ubuntu or a system sans;
the photo overview uses a Georgia-style serif. Page assets include five small original floor
plans, profile thumbnails and images attached to notice-board/chat entries. No album/archive
photos were downloaded. Floor plans are low-resolution originals and must be printed small.

## Duplicate handling

Fragments, sorting and category filters were canonicalized to the primary view. Bounded
pagination remains distinct. Shared navigation is excluded from cleaned main content.
'''
report+=f'\nExact main-content duplicates: {json.dumps(exact,ensure_ascii=False)}.\n'
report+='The empty G. A. Sportsmann, GAHKroom and M.H.G.A pages are near-duplicates except for their channel names. Notice previews and their full detail pages intentionally overlap; the book uses full source text where quoted.\n'
report+='\n## Captured page index\n\n| Local identifier | Original URL |\n|---|---|\n'
for r in index['pages']:report+=f"| {r['id']} | {r['url']} |\n"
(ROOT/'ARCHIVE_REPORT.md').write_text(report)
print(f"Final archive: {len(index['pages'])} pages; {len(index['failures'])} unresolved failures.")
