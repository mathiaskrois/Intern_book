# INTERN — til Anton

A private, 32-page editorial interpretation of GAHK Intern, captured on 27 September 2026.
The book represents the website's main sections. The wiki is excluded; Fotoalbum and Arkiv
appear only as overview pages, without their stored photos or files.

The second gift edition, revised 28 September 2026, adds a bold typographic cover,
a dedication and monogram for Anton, varied chapter colors, conversation cards and clearer tables.
The requested name adaptation applies throughout the book, including the dashboard excerpt.
Original archive files remain unchanged; the colophon explains the personalization.

## Finished files

- `book/output/book-a5.pdf` — sequential 148 × 210 mm pages.
- `book/output/book-a4-booklet.pdf` — imposed A4 landscape booklet, eight duplex sheets.
- `book/output/PRINTING.md` — exact print settings and folding order.
- `book/output/QA_REPORT.md` — final validation and visual inspection record.
- `ARCHIVE_REPORT.md` — scoped capture totals, exclusions and the one unavailable source image.

For the imposed PDF, print **A4 landscape, duplex, flip on short edge, actual size / 100%,
one PDF page per sheet**. Do not impose it a second time with a printer's Booklet option.

## Editable source

`book/src/book.html`, `book/src/book.css` and `book/src/edition.css` are the editable book. All print dependencies
are local. `book/src/page-manifest.json` maps each book page to its archived source URLs.
`book/build.py` reconstructs the HTML from the archive and the editorial page definitions.

To render an edited HTML/CSS file, run:

```sh
.venv/bin/python book/render.py
```

To rebuild the HTML from the editorial generator, then render it:

```sh
.venv/bin/python book/build.py
.venv/bin/python book/render.py
```

Rebuilding overwrites direct edits to `book/src/book.html`; edit `book/build.py` when changes
must survive regeneration. The renderer writes page images, contact sheets, geometry/font
audits and the imposition manifest under `book/qa/`. It runs Chromium locally and makes no
network requests. A fresh environment needs Python, Google Chrome and `requirements.txt`.

The local fonts and SIL Open Font License texts are in `book/assets/fonts/`. Static instances
are used for reliable PDF font embedding; the original variable fonts are retained alongside them.

## Archive

`website-archive/index.json` indexes 58 HTML pages, their original URLs, relationships,
outgoing links, screenshots, text and assets. The archive is broader than the printed selection.
The source archive is kept separate from all book-specific screenshot crops and typography.

The crawler uses only read-only navigation after authentication. It does not send messages,
react, edit records or submit application/account forms. It blocks subsequent non-GET requests.
It intentionally limits repeated directory/room records, history and filter combinations.
The external calendar embed is not captured; the site's own event pages are.

Credentials are loaded in memory from environment variables or `.env`, with the supplied
local RTF brief as a fallback. Persistent browser authentication stays under `.auth/`.
The brief, credentials, sessions and private generated content are excluded from Git.
Nothing has been committed or published.

To take a new dated snapshot, first keep a separate copy of the existing archive and book;
then run `crawler/archive.py` followed by `crawler/finalize_archive.py`. A new snapshot can
change or remove ephemeral source messages, so review the editorial selections before rebuilding.
