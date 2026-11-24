"""Build the static website from content.json and the shared assets."""

from argparse import ArgumentParser
from datetime import date
from html import escape
import json
from pathlib import Path
from shutil import copy2, copytree

SOURCE = Path(__file__).resolve().parent
SITE_ROOT = SOURCE.parent
ORIGIN = "https://sinagolara.com/"
DATA = json.loads((SOURCE / "content.json").read_text(encoding="utf-8"))
PERSON = DATA["person"]
PAGES = {"home": "Home", "research": "Research", "teaching": "Teaching", "media": "Media"}


def text(value):
    return escape(str(value), quote=True)


def link(href, label, css_class="", new_tab=False):
    classes = f' class="{css_class}"' if css_class else ""
    target = ' target="_blank" rel="noopener noreferrer"' if new_tab else ""
    return f'<a href="{text(href)}"{classes}{target}>{text(label)}</a>'


def person_schema():
    details = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": PERSON["name"],
        "jobTitle": PERSON["title"],
        "affiliation": {"@type": "CollegeOrUniversity", "name": PERSON["institution"]},
        "url": ORIGIN,
        "image": ORIGIN + PERSON["portrait"],
        "sameAs": [
            PERSON["profile"], PERSON["linkedin"], PERSON["x"],
            "https://orcid.org/0000-0001-5674-0647",
        ],
    }
    return json.dumps(details, ensure_ascii=False).replace("<", "\\u003c")


def layout(page, description, body):
    base = "./" if page == "home" else "../"
    canonical = ORIGIN if page == "home" else ORIGIN + page + "/"
    title = (
        f"{PERSON['name']} | Supply Chain and Operations Management"
        if page == "home" else f"{PAGES[page]} | {PERSON['name']}"
    )
    image = ORIGIN + PERSON["portrait"]
    nav = []
    for key, label in PAGES.items():
        destination = base if key == "home" else base + key + "/"
        current = ' aria-current="page"' if key == page else ""
        nav.append(f'<a href="{destination}"{current}>{label}</a>')
    nav.append(link(base + PERSON["cv"], "CV (PDF)", "nav-cv", new_tab=True))
    bio_schema = (
        f'<script type="application/ld+json">{person_schema()}</script>'
        if page == "home" else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{text(title)}</title>
  <meta name="description" content="{text(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{text(PERSON['name'])}">
  <meta property="og:title" content="{text(title)}">
  <meta property="og:description" content="{text(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:alt" content="Portrait of {text(PERSON['name'])}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{text(title)}">
  <meta name="twitter:description" content="{text(description)}">
  <meta name="twitter:image" content="{image}">
  <meta name="twitter:image:alt" content="Portrait of {text(PERSON['name'])}">
  <link rel="icon" type="image/png" href="{base}assets/favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Lora:wght@400;500;600;700&amp;display=swap">
  <link rel="stylesheet" href="{base}assets/site.css">
  <script src="{base}assets/site.js" defer></script>
  {bio_schema}
</head>
<body data-page="{page}">
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="site-width header-inner">
      {link(base, PERSON['name'], 'wordmark')}
      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav" hidden>Menu</button>
      <nav id="site-nav" class="site-nav" aria-label="Main navigation">
        {" ".join(nav)}
        <button class="theme-toggle" type="button" aria-pressed="false" hidden>Dark mode</button>
      </nav>
    </div>
  </header>
  <main id="main" tabindex="-1">
{body}
  </main>
  <footer class="site-footer">
    <div class="site-width footer-inner">
      <div class="footer-identity">
        <p class="footer-name">{text(PERSON['name'])}</p>
        <p>{text(PERSON['school'])}<br>{text(PERSON['institution'])}</p>
      </div>
      <div class="footer-links" aria-label="Contact and profiles">
        {link('mailto:' + PERSON['email'], 'Media inquiries' if page == 'media' else PERSON['email'], 'footer-email')}
        <ul class="plain-list">
          <li>{link(PERSON['profile'], 'GSU profile', new_tab=True)}</li>
          <li>{link(PERSON['linkedin'], 'LinkedIn', new_tab=True)}</li>
          <li>{link(PERSON['x'], 'X', new_tab=True)}</li>
        </ul>
      </div>
    </div>
  </footer>
</body>
</html>
"""


def publication_summary(item, url):
    summary = text(item["summary"])
    abstract = item.get("abstract")
    overview = item.get("abstract_overview")
    if not abstract and not overview:
        return f'<p class="item-summary">{summary}</p>'

    label = "Abstract" if abstract else "Abstract overview"
    original = link(url, "Read the publisher’s abstract", new_tab=True) if overview and not abstract else ""
    return f"""
          <details class="publication-abstract">
            <summary class="abstract-toggle">
              <span>{summary}<span class="sr-only"> {label}</span></span>
              <span class="abstract-icon" aria-hidden="true">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="M5 10h10"/>
                  <path class="abstract-plus" d="M10 5v10"/>
                </svg>
              </span>
            </summary>
            <div class="abstract-content">
              <p class="abstract-label">{label}</p>
              <p>{text(abstract or overview)}</p>
              {original}
            </div>
          </details>"""


def publication(item, *, compact=False):
    url = "https://doi.org/" + item["doi"] if "doi" in item else item["publisher_url"]
    full_reference = f" · {text(item['reference'])}" if not compact else ""
    attrs = "" if compact else f' id="{text(item["id"])}" data-sort="{item["year"]}"'
    return f"""
      <li class="publication"{attrs}>
        <article>
          <p class="item-meta">{text(item['journal'])} <span aria-hidden="true">·</span>
            {item['year']}{full_reference}</p>
          <h3>{link(url, item['title'], new_tab=True)}</h3>
          <p class="authors">{text(item['authors'])}</p>
          {publication_summary(item, url)}
        </article>
      </li>"""

def media_item(item, base, *, compact=False):
    published = item.get("date", "")
    date_markup = ""
    if published:
        month_only = len(published) == 7
        day = date.fromisoformat(published + "-01" if month_only else published)
        label = day.strftime("%b %Y") if month_only else f"{day.strftime('%b')} {day.day}, {day.year}"
        date_markup = f' <span aria-hidden="true">·</span> <time datetime="{published}">{label}</time>'
    image = ""
    if "image" in item:
        image = f"""
          <a href="{text(item['url'])}" class="media-image" tabindex="-1" aria-hidden="true" target="_blank" rel="noopener noreferrer">
            <img src="{base + text(item['image'])}" alt="" loading="lazy" decoding="async" width="480" height="270">
          </a>"""
    attrs = "" if compact else f' id="{text(item["id"])}" data-sort="{published}"'
    return f"""
      <li class="media-item"{attrs}>
        <article class="media-entry{' has-thumbnail' if image else ''}">{image}
          <div class="media-copy">
            <p class="item-meta">{text(item['outlet'])}{date_markup}
              <span aria-hidden="true">·</span> {text(item['format'])}</p>
            <h3>{link(item['url'], item['title'], new_tab=True)}</h3>
            <p class="item-summary">{text(item['summary'])}</p>
          </div>
        </article>
      </li>"""


def featured(key):
    entries = {item["id"]: item for item in DATA[key]}
    return [entries[id_] for id_ in DATA[f"featured_{key}"]]


def award(item):
    announcement = (
        f"<p>{link(item['url'], 'Award announcement', new_tab=True)}</p>" if "url" in item else ""
    )
    return f"""
            <li>
              <strong>{text(item['title'])}</strong>
              <p class="item-meta">{text(item['organization'])}</p>
              <p>{text(item['description'])}</p>
              {announcement}
            </li>"""


def homepage():
    working = DATA["working_paper"]
    awards = "".join(award(item) for item in DATA["honors"])
    papers = "".join(publication(item, compact=True) for item in featured("publications"))
    news = "".join(media_item(item, "./", compact=True) for item in featured("media"))
    paragraphs = "\n".join(f"          <p>{text(paragraph)}</p>" for paragraph in PERSON["bio"])
    return f"""
    <section class="hero" id="home" aria-labelledby="person-name">
      <div class="site-width hero-inner">
        <div class="hero-copy">
          <p class="role">{text(PERSON['title'])}</p>
          <h1 id="person-name">{text(PERSON['name'])}</h1>
          <p class="affiliation">{text(PERSON['school'])}<br>{text(PERSON['institution'])}</p>
          <p class="intro">{text(PERSON['intro'])}</p>
          <div class="hero-actions">
            {link('./research/', 'Explore research', 'button button-primary')}
            {link('./' + PERSON['cv'], 'CV (PDF)', 'button button-outline', new_tab=True)}
          </div>
          <p class="hero-contact">{link('mailto:' + PERSON['email'], PERSON['email'])}</p>
        </div>
        <figure class="portrait">
          <img src="./{text(PERSON['portrait'])}" alt="Portrait of {text(PERSON['name'])}" width="632" height="788" fetchpriority="high">
        </figure>
      </div>
    </section>
    <div class="site-width home-highlights">
      <section aria-labelledby="selected-research">
        <div class="section-heading">
          <h2 id="selected-research">Selected research</h2>
          {link('./research/', 'All publications', 'section-link')}
        </div>
        <ul class="plain-list publication-list compact-publications">{papers}
        </ul>
        <article class="home-working">
          <p class="item-meta">Working paper</p>
          <h3>{link('./research/#working-papers', working['title'])}</h3>
          <p class="item-summary">{text(working['status'])}</p>
        </article>
      </section>
      <section class="home-media" aria-labelledby="selected-media">
        <div class="section-heading">
          <h2 id="selected-media">In the media</h2>
          {link('./media/', 'All media', 'section-link')}
        </div>
        <ul class="plain-list media-list compact-media">{news}
        </ul>
      </section>
    </div>
    <section id="about" class="about">
      <div class="site-width about-inner">
        <h2>About</h2>
        <div class="about-copy">
{paragraphs}
          <p>{link(PERSON['profile'], 'Georgia State faculty profile', 'section-link', new_tab=True)}</p>
          <section class="honors" aria-labelledby="honors-heading">
            <h3 id="honors-heading">Honors and awards</h3>
            <ul class="plain-list">{awards}</ul>
          </section>
        </div>
      </div>
    </section>"""


def chronological_sort(identifier, label):
    return f"""
          <button id="{identifier}-sort" class="chronological-sort" type="button"
                  aria-controls="{identifier}" aria-label="Sort {text(label.lower())} oldest first"
                  title="Sort oldest first" data-order="newest" data-sort-label="{text(label)}" hidden>
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M3 5h10M3 11h7M3 17h4"/>
              <path class="sort-direction" d="M18 5v14m-3-3 3 3 3-3"/>
            </svg>
          </button>
          <p id="{identifier}-sort-status" class="sr-only" role="status"></p>"""

def page_intro(title, description):
    return f"""
    <div class="page-intro">
      <h1>{title}</h1>
      <p>{description}</p>
    </div>"""


def research_page():
    working = DATA["working_paper"]
    papers = sorted(DATA["publications"], key=lambda item: item["year"], reverse=True)
    rows = "".join(publication(item) for item in papers)
    summary = "Empirical research on digital platforms, retail and service operations, and supply chains."
    return f"""
    <div class="site-width page">
      {page_intro('Research', summary)}
      <section aria-labelledby="publications-heading">
        <div class="section-heading sortable-heading">
          <h2 id="publications-heading">Selected publications</h2>
          {chronological_sort('publications', 'Publications')}
        </div>
        <ul id="publications" class="plain-list publication-list">{rows}
        </ul>
      </section>
      <section id="working-papers" class="research-working" aria-labelledby="working-heading">
        <h2 id="working-heading">Working papers</h2>
        <article class="working-paper">
          <h3>{text(working['title'])}</h3>
          <p class="authors">{text(working['authors'])}</p>
          <p class="item-summary">{text(working['summary'])}</p>
          <p class="item-meta">{text(working['status'])}</p>
        </article>
      </section>
    </div>"""


def teaching_group(record):
    school = f'<p>{text(record["school"])}</p>' if "school" in record else ""
    group_class = "course-group course-current" if record.get("current") else "course-group"
    courses = "".join(f"""
          <li class="course-row">
            <span class="course-code">{text(code)}</span>
            <strong>{text(title)}</strong>
            <span class="course-level">{text(level)}</span>
          </li>""" for code, title, level in record["courses"])
    return f"""
        <li class="{group_class}" data-sort="{record['start_year']}">
          <div class="course-group-heading">
            <div>
              <h3>{text(record['institution'])}</h3>
              {school}
            </div>
            <p>{text(record['dates'])}</p>
          </div>
          <ul class="plain-list course-list">{courses}
          </ul>
        </li>"""


def dissertation(item):
    title = link(item["url"], item["title"], new_tab=True) if "url" in item else text(item["title"])
    return f"""
          <li>
            <h3>{title}</h3>
            <p>{text(item['name'])} · {text(item['role'])}</p>
            <p class="item-meta">{text(item['institution'])}</p>
          </li>"""


def teaching_page():
    groups = sorted(DATA["teaching"], key=lambda item: item["start_year"], reverse=True)
    courses = "".join(teaching_group(item) for item in groups)
    talk = DATA["invited_talk"]
    dissertations = "".join(dissertation(item) for item in DATA["dissertations"])
    advising = "".join(
        f'<li><h3>{text(title)}</h3><p>{text(role)}</p></li>'
        for title, role in DATA["mentorship"]
    )
    return f"""
    <div class="site-width page teaching-page">
      {page_intro('Teaching &amp; mentorship', 'Courses in operations and supply chain strategy, doctoral dissertation service, and graduate capstone advising.')}
      <section class="teaching-section" aria-labelledby="courses-heading">
        <div class="section-heading sortable-heading">
          <h2 id="courses-heading">Courses</h2>
          {chronological_sort('teaching-courses', 'Courses')}
        </div>
        <ul id="teaching-courses" class="plain-list teaching-courses">{courses}
        </ul>
      </section>
      <section class="teaching-section mentorship" aria-labelledby="dissertation-service">
        <h2 id="dissertation-service">Doctoral dissertation service</h2>
        <ul class="plain-list mentorship-list">{dissertations}</ul>
      </section>
      <section class="teaching-section mentorship" aria-labelledby="advising">
        <h2 id="advising">Graduate capstone advising</h2>
        <p>MIT Center for Transportation &amp; Logistics · 2018–2019</p>
        <ul class="plain-list mentorship-list">{advising}</ul>
      </section>
      <section class="teaching-section" aria-labelledby="invited-talks">
        <h2 id="invited-talks">Invited talks</h2>
        <article class="working-paper">
          <h3>{text(talk['title'])}</h3>
          <p class="item-meta">{text(talk['role'])}</p>
          <p>{text(talk['organization'])}</p>
          <p class="item-summary">{text(talk['summary'])}</p>
        </article>
      </section>
    </div>"""


def media_page():
    records = sorted(DATA["media"], key=lambda item: item.get("date", ""), reverse=True)
    cards = "".join(media_item(item, "../") for item in records)
    return f"""
    <div class="site-width page">
      {page_intro('Media', 'Interviews and coverage on supply chains, trade, and retail.')}
      <section aria-labelledby="coverage">
        <div class="section-heading sortable-heading">
          <h2 id="coverage">Selected coverage</h2>
          {chronological_sort('media-items', 'Media coverage')}
        </div>
        <ul id="media-items" class="plain-list media-list media-grid">{cards}
        </ul>
      </section>
    </div>"""


def build(output):
    sections = {
        "home": (
            f"{PERSON['name']}, Assistant Professor of Supply Chain Management at Georgia State University. Research, teaching, and media.",
            homepage(),
        ),
        "research": ("Selected publications by Sina Golara on retail, services, and supply chains.", research_page()),
        "teaching": ("Operations and supply chain management courses and graduate capstone advising by Sina Golara.", teaching_page()),
        "media": ("Selected interviews and media coverage featuring Sina Golara.", media_page()),
    }
    for page, (description, content) in sections.items():
        directory = output if page == "home" else output / page
        directory.mkdir(parents=True, exist_ok=True)
        lines = layout(page, description, content).splitlines()
        markup = "\n".join(line.rstrip() for line in lines) + "\n"
        (directory / "index.html").write_text(markup, encoding="utf-8")
    if output.resolve() != SITE_ROOT:
        for directory in ("assets", "Images"):
            copytree(SITE_ROOT / directory, output / directory, dirs_exist_ok=True)
        copy2(SITE_ROOT / PERSON["cv"], output / PERSON["cv"])


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=SITE_ROOT,
                        help="Directory for the generated site (defaults to the repository root)")
    build(parser.parse_args().output)
