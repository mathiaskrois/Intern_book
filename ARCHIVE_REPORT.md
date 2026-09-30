# Website archive report

Captured 27 September 2026 using the supplied account and a persistent Chromium profile.
This is a bounded snapshot of GAHK Intern, revised to match the user's explicit scope:
the wiki is excluded; Fotoalbum and Arkiv are represented only by their overview pages.
No photos or documents stored inside those two sections were archived or used in the book.

## Capture totals

- 58 unique HTML pages.
- 38 distinct page asset URLs (images and CSS).
- 3 event calendar downloads.
- 0 unresolved page failures.
- Limit: 100 pages and 3 pagination pages; the queue was exhausted before the limit.

## Hierarchy and coverage

- `dashboard`: 1 page(s).
- `opslagstavle`: 13 page(s).
- `den-hurtige`: 19 page(s).
- `begivenheder`: 5 page(s).
- `alumneliste`: 1 page(s).
- `fotoalbum`: 1 page(s).
- `soegvaerelse`: 1 page(s).
- `vaerelsestjek`: 2 page(s).
- `ak`: 1 page(s).
- `oelkaelder`: 1 page(s).
- `reparationer`: 9 page(s).
- `stamtree`: 1 page(s).
- `statistik`: 1 page(s).
- `arkiv`: 1 page(s).
- `beboer`: 1 page(s).

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

Exact main-content duplicates: [].
The empty G. A. Sportsmann, GAHKroom and M.H.G.A pages are near-duplicates except for their channel names. Notice previews and their full detail pages intentionally overlap; the book uses full source text where quoted.

## Captured page index

| Local identifier | Original URL |
|---|---|
| dashboard | https://www.gahk.dk/intern/ |
| opslagstavle | https://www.gahk.dk/intern/opslagstavle/ |
| den-hurtige | https://www.gahk.dk/intern/den-hurtige/ |
| begivenheder | https://www.gahk.dk/intern/begivenheder/ |
| alumneliste | https://www.gahk.dk/intern/alumneliste/ |
| fotoalbum | https://www.gahk.dk/intern/fotoalbum/ |
| soegvaerelse | https://www.gahk.dk/intern/soegvaerelse/ |
| vaerelsestjek | https://www.gahk.dk/intern/vaerelsestjek/ |
| ak | https://www.gahk.dk/intern/ak/ |
| oelkaelder-min-saldo | https://www.gahk.dk/intern/oelkaelder/min-saldo |
| reparationer | https://www.gahk.dk/intern/reparationer/ |
| stamtree | https://www.gahk.dk/intern/stamtree/ |
| statistik | https://www.gahk.dk/intern/statistik/ |
| arkiv | https://www.gahk.dk/intern/arkiv/ |
| beboer-456-profil | https://www.gahk.dk/intern/beboer/456/profil |
| begivenheder-4 | https://www.gahk.dk/intern/begivenheder/4 |
| opslagstavle-15 | https://www.gahk.dk/intern/opslagstavle/15 |
| opslagstavle-14 | https://www.gahk.dk/intern/opslagstavle/14 |
| opslagstavle-13 | https://www.gahk.dk/intern/opslagstavle/13 |
| opslagstavle-12 | https://www.gahk.dk/intern/opslagstavle/12 |
| opslagstavle-11 | https://www.gahk.dk/intern/opslagstavle/11 |
| opslagstavle-10 | https://www.gahk.dk/intern/opslagstavle/10 |
| opslagstavle-9 | https://www.gahk.dk/intern/opslagstavle/9 |
| opslagstavle-8 | https://www.gahk.dk/intern/opslagstavle/8 |
| opslagstavle-7 | https://www.gahk.dk/intern/opslagstavle/7 |
| opslagstavle-6 | https://www.gahk.dk/intern/opslagstavle/6 |
| opslagstavle-2 | https://www.gahk.dk/intern/opslagstavle/2 |
| opslagstavle-1 | https://www.gahk.dk/intern/opslagstavle/1 |
| den-hurtige-tv-rezz | https://www.gahk.dk/intern/den-hurtige/tv-rezz |
| den-hurtige-sportsmann | https://www.gahk.dk/intern/den-hurtige/sportsmann |
| den-hurtige-gahkroom | https://www.gahk.dk/intern/den-hurtige/gahkroom |
| den-hurtige-mhga | https://www.gahk.dk/intern/den-hurtige/mhga |
| den-hurtige-170-traad | https://www.gahk.dk/intern/den-hurtige/170/traad |
| den-hurtige-171-traad | https://www.gahk.dk/intern/den-hurtige/171/traad |
| den-hurtige-173-traad | https://www.gahk.dk/intern/den-hurtige/173/traad |
| den-hurtige-174-traad | https://www.gahk.dk/intern/den-hurtige/174/traad |
| den-hurtige-175-traad | https://www.gahk.dk/intern/den-hurtige/175/traad |
| den-hurtige-176-traad | https://www.gahk.dk/intern/den-hurtige/176/traad |
| den-hurtige-177-traad | https://www.gahk.dk/intern/den-hurtige/177/traad |
| den-hurtige-178-traad | https://www.gahk.dk/intern/den-hurtige/178/traad |
| den-hurtige-180-traad | https://www.gahk.dk/intern/den-hurtige/180/traad |
| den-hurtige-181-traad | https://www.gahk.dk/intern/den-hurtige/181/traad |
| den-hurtige-182-traad | https://www.gahk.dk/intern/den-hurtige/182/traad |
| den-hurtige-183-traad | https://www.gahk.dk/intern/den-hurtige/183/traad |
| den-hurtige-187-traad | https://www.gahk.dk/intern/den-hurtige/187/traad |
| begivenheder-kalender | https://www.gahk.dk/intern/begivenheder/kalender |
| vaerelsestjek-se-101 | https://www.gahk.dk/intern/vaerelsestjek/se/101 |
| reparationer-arkiv | https://www.gahk.dk/intern/reparationer/arkiv |
| reparationer-3 | https://www.gahk.dk/intern/reparationer/3 |
| reparationer-4 | https://www.gahk.dk/intern/reparationer/4 |
| reparationer-5 | https://www.gahk.dk/intern/reparationer/5 |
| reparationer-6 | https://www.gahk.dk/intern/reparationer/6 |
| reparationer-7 | https://www.gahk.dk/intern/reparationer/7 |
| reparationer-2 | https://www.gahk.dk/intern/reparationer/2 |
| reparationer-1 | https://www.gahk.dk/intern/reparationer/1 |
| den-hurtige-188-traad | https://www.gahk.dk/intern/den-hurtige/188/traad |
| begivenheder-1 | https://www.gahk.dk/intern/begivenheder/1 |
| begivenheder-2 | https://www.gahk.dk/intern/begivenheder/2 |
