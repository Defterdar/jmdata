"""One-off migration: converts the exported WordPress JSON (../_export) into a static site."""
import html, json, os, re, shutil, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "_export")
HOST = re.compile(r"https?://(?:www\.)?jmdata\.dk", re.I)
SKIP = {"kunder", "brugeroprettelse-minus-ftx", "cookie-politik", "kontakt-formular", "diverse", "produkter", "artikler"}
APPS = [
    "JM-Data-fjernsupport.exe",
    "JM-Data-Fjernsupport.dmg",
    "rustdesk-host=help.jmdata.dk,key=1eqFAAv5fRA3yT4T6qCvC1o2mrXeRvE6tFIzJAQ3OO4=.exe",
]


def load(n):
    with open(os.path.join(EXP, n + ".json"), encoding="utf-8-sig") as f:
        return json.load(f)


pages, posts = load("pages"), load("posts")


def fetch(url, dest):
    full = os.path.join(ROOT, dest)
    if os.path.exists(full):
        return
    os.makedirs(os.path.dirname(full), exist_ok=True)
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?=&,%@"), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r, open(full, "wb") as o:
        shutil.copyfileobj(r, o)


def path_of(link):
    return urllib.parse.urlparse(link).path.strip("/")


def rel(frm, to):
    """Relative URL from page at path `frm` (dir) to site-root path `to`."""
    depth = len([p for p in frm.split("/") if p])
    return "../" * depth + to if (depth or to) else "./"


def fix(content, here):
    content = re.sub(r"<script.*?</script>|<style.*?</style>|<aside.*?</aside>", "", content, flags=re.S)
    content = re.sub(r'\s(srcset|sizes)="[^"]*"', "", content)

    def sub(m):
        url = m.group(2)
        if not HOST.match(url):
            return m.group(0)
        p = urllib.parse.unquote(HOST.sub("", url)).split("#")[0]
        frag = "#" + url.split("#", 1)[1] if "#" in url else ""
        if p.startswith("/wp-content/") or p.startswith("/apps/"):
            dest = "assets/" + p.split("/", 2)[2] if p.startswith("/wp-content/") else p.lstrip("/")
            try:
                fetch(url.split("#")[0], dest)
            except Exception as e:
                print("WARN download", url, e)
                return m.group(0)
            return f'{m.group(1)}="{rel(here, urllib.parse.quote(dest, safe="/=,@"))}{frag}"'
        target = p.strip("/")
        if target == "cookie-politik":
            target = "cookie-og-privatlivspolitik"
        if target == "kontakt/kontakt-formular":
            target = "kontakt"
        return f'{m.group(1)}="{rel(here, target + "/" if target else "")}{frag}"'

    return re.sub(r'(href|src)="\s*([^"]+?)\s*"', sub, content)


NAV_PRODUCTS = sorted([p for p in pages if path_of(p["link"]).startswith("produkter/")], key=lambda x: x["menu_order"])
NAV_DIVERSE = sorted([p for p in pages if path_of(p["link"]).startswith("diverse/")], key=lambda x: x["menu_order"])


def layout(here, title, body, desc="", crumbs=None):
    r = lambda t: rel(here, t)
    item = lambda p: f'<li><a href="{r(path_of(p["link"]))}/">{html.unescape(p["title"]["rendered"])}</a></li>'
    prods = "".join(item(p) for p in NAV_PRODUCTS)
    divs = "".join(item(p) for p in NAV_DIVERSE)
    side = "".join(f'<li><a href="{r(path_of(p["link"]))}/">{p["title"]["rendered"]}</a></li>' for p in posts[:4])
    home = here == ""
    if home:
        top = f"""<div class="hero">
  <img class="hero-bg" src="{r('assets/2021/05/slide_binary5.jpg')}" alt="">
  <a class="hero-btn" style="margin-left:-465px" href="{r('produkter/dynamics-365-business-central/')}" title="Business Central"><img src="{r('assets/2020/05/frontknap_BC_txt_rotate3.png')}" alt="Business Central"></a>
  <a class="hero-btn" style="margin-left:-125px" href="{r('produkter/microsoft-365/')}" title="Microsoft 365"><img src="{r('assets/2020/05/frontknap_365_txt_rotate3.png')}" alt="Microsoft 365"></a>
  <a class="hero-btn" style="margin-left:215px" href="{r('produkter/microsoft-azure/')}" title="Microsoft Azure"><img src="{r('assets/2020/05/frontknap_msazure_txt_rotate4.png')}" alt="Microsoft Azure"></a>
</div>"""
    else:
        trail = f'<a href="{r("")}">Hjem</a>'
        for label, href in (crumbs or []):
            trail += f' <span class="sep">/</span> <a href="{r(href)}">{label}</a>'
        trail += f' <span class="sep">/</span> <span class="cur">{html.escape(title)}</span>'
        top = f'<div class="page-top"><div class="wrap"><h1>{html.escape(title)}</h1><div class="crumbs">{trail}</div></div></div>'
    icon = lambda href, t, img, ext="": f'<a href="{href}" title="{t}"{ext}><img src="{r("assets/images/" + img)}" width="18" height="18" alt="{t}"></a>'
    return f"""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title) + " – JM Data, Ikast ApS" if title != "JM Data, Ikast ApS" else "JM Data, Ikast ApS – Store it løsninger til små penge"}</title>
<meta name="description" content="{html.escape(desc or 'JM Data, Ikast ApS - Store it løsninger til små penge')}">
<link rel="icon" href="{r('assets/2018/10/favicon.ico')}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Open+Sans:400,600,700">
<link rel="stylesheet" href="{r('assets/style.css')}?v=4">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="{r('')}" title="JM Data, Ikast ApS - Store it løsninger til små penge"><img src="{r('assets/images/headerlogo.png')}" alt="JM Data, Ikast ApS"></a>
    <div class="head-right">
      <div class="icons">
        {icon(r('cookie-og-privatlivspolitik/'), 'Cookie- og privatlivspolitik', 'privacy.png')}
        {icon(r('oversigt/'), 'Oversigt', 'sitemap.png')}
        {icon('https://backup.jmdata.dk/', 'JM Data Online Backup', 'backup.png', ' target="_blank"')}
        {icon('https://cloud.jmdata.dk/RDWeb/WebClient/', 'JM Data Remote Desktop', 'desktop.png', ' target="_blank"')}
      </div>
      <nav>
        <ul>
          <li><a href="{r('produkter/')}">Produkter <i class="chev"></i></a><ul>{prods}</ul></li>
          <li><a href="{r('artikler/')}">Artikler</a></li>
          <li><a href="{r('diverse/')}">Diverse <i class="chev"></i></a><ul>{divs}
            <li><a href="{r('apps/JM-Data-fjernsupport.exe')}">Fjernsupport for PC</a></li>
            <li><a href="{r('apps/JM-Data-Fjernsupport.dmg')}">Fjernsupport for Mac</a></li>
            <li><a href="{r('apps/rustdesk-host=help.jmdata.dk,key=1eqFAAv5fRA3yT4T6qCvC1o2mrXeRvE6tFIzJAQ3OO4=.exe')}">RustDesk for PC</a></li></ul></li>
          <li><a href="{r('kontakt/')}">Kontakt</a></li>
          <li><a href="{r('apps/JM-Data-fjernsupport.exe')}" title="Klik venligst her for JM Data fjernsupport">&rarr;&nbsp; Fjernsupport</a></li>
        </ul>
      </nav>
    </div>
  </div>
</header>
{top}
<div class="wrap layout">
<main>
{body}
</main>
<aside class="sidebar">
  <h3>Artikler</h3>
  <ul class="side-list">{side}</ul>
  <img class="partner" src="{r('assets/2022/11/microsoft-partner-grey.png')}" alt="Microsoft Partner">
</aside>
</div>
<footer class="site-footer">
  <div class="wrap">
    <p class="links"><a href="{r('cookie-og-privatlivspolitik/')}">Cookie- og privatlivspolitik</a> &nbsp;|&nbsp; <a href="{r('betingelser/')}">Betingelser</a> &nbsp;|&nbsp; <a href="{r('oversigt/')}">Oversigt</a></p>
    <div class="bottom">
      <a href="{r('')}"><img src="{r('assets/2018/10/footerlogo.png')}" alt="JM Data, Ikast ApS"></a>
      <span>Copyright &copy; JM Data, Ikast ApS &middot; Navervej 15 &middot; DK-7430 Ikast &middot; Telefon +45 3049 7257 &middot; E-mail <a href="mailto:kontakt@jmdata.dk">kontakt@jmdata.dk</a> &middot; CVR 25064216</span>
    </div>
  </div>
</footer>
</body>
</html>
"""

def crumbs_for(here):
    parts = here.split('/')
    return [(parts[0].capitalize(), parts[0] + '/')] if len(parts) > 1 else []


def write(path, content, name="index.html"):
    full = os.path.join(ROOT, path, name) if path else os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def listing(items, here):
    out = ['<ul class="post-list">']
    for it in items:
        ex = it.get("excerpt", {}).get("rendered", "").replace("<!--more-->", "")
        out.append(f'<li><a href="{rel(here, path_of(it["link"]))}/">{it["title"]["rendered"]}</a>{fix(ex, here)}</li>')
    out.append("</ul>")
    return "\n".join(out)


for a in APPS:
    try:
        fetch("https://jmdata.dk/apps/" + a, "apps/" + a)
    except Exception as e:
        print("WARN app", a, e)

for p in pages:
    if p["slug"] in SKIP:
        continue
    here = path_of(p["link"])
    body = fix(p["content"]["rendered"], here)
    title = html.unescape(p["title"]["rendered"])
    if here == "diverse/min-ip":
        body = ('<p>Din offentlige IP-adresse er: <strong id="ip">henter…</strong></p>\n'
                '<script>fetch("https://api.ipify.org?format=json").then(r=>r.json())'
                '.then(d=>{document.getElementById("ip").textContent=d.ip}).catch(()=>{document.getElementById("ip").textContent="kunne ikke hentes"});</script>')
    if here == "oversigt":
        body = re.sub(r'<a href="[^"]*kategori/[^"]*">(.*?)</a>', r"\1", body)
        body = re.sub(r'<li class="page_item page-item-1552">.*?</li>\n', "", body)
    if here == "kontakt":
        body += '<p>Skriv gerne til <a href="mailto:kontakt@jmdata.dk">kontakt@jmdata.dk</a>.</p>'
    if here == "":
        title = "JM Data, Ikast ApS"
    write(here, layout(here, title, body, crumbs=crumbs_for(here)))

for po in posts:
    here = path_of(po["link"])
    body = f'<p class="meta">{po["date"][:10]}</p>' + fix(po["content"]["rendered"], here)
    write(here, layout(here, html.unescape(po["title"]["rendered"]), body, crumbs=[("Artikler", "artikler/")]))

write("artikler", layout("artikler", "Artikler", listing(posts, "artikler")))
write("produkter", layout("produkter", "Produkter", listing(NAV_PRODUCTS, "produkter")))
dl = "".join(f'<li><a href="../apps/{urllib.parse.quote(a, safe="=,@")}">{n}</a></li>' for a, n in zip(APPS, ["Fjernsupport for PC", "Fjernsupport for Mac", "RustDesk for PC"]))
write("diverse", layout("diverse", "Diverse", listing(NAV_DIVERSE, "diverse") + '<h2>Downloads</h2><ul class="post-list">' + dl + "</ul>"))
write("", layout("", "Siden blev ikke fundet", '<p>Siden findes ikke. <a href="/">Gå til forsiden</a>.</p>'), "404.html")
open(os.path.join(ROOT, ".nojekyll"), "w").close()
print("done")




