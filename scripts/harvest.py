#!/usr/bin/env python3
"""Collecte les offres d'emploi récentes (CDI, CDD, intérim; hors alternance/stage)
publiées sur candidat.francetravail.fr et écrit offres.json.

Usage: python3 -I harvest.py OUT.json [recherches.json] [--par-dept N] [--par-recherche N]
recherches.json = [{"mots": "assistant rh", "dept": "69"}, ...]
Rythme volontairement lent (une requête par seconde environ).
"""
import urllib.error, sys, json, re, time, html, http.cookiejar, urllib.request, urllib.parse, datetime

BASE = "https://candidat.francetravail.fr"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
DEPTS = [f"{i:02d}" for i in range(1, 96) if i != 20] + ["2A", "2B", "971", "972", "973", "974", "976"]
FREE = re.compile(r"ind[ée]pendant|freelance|free-lance|vacata|auto-?entrepreneur|micro-?entrepr|portage salarial|lib[ée]ral|prestataire|sous-traitan|\bjury\b|examinat|[ée]valuateur|correcteur|surveillant d.examen|sessions? d.examen", re.I)
EXCLU = re.compile(r"alternan|apprenti|professionnalisation|\bstage\b|stagiaire|formation qualifiante|\bpoei\b", re.I)

def opener():
    cj = http.cookiejar.CookieJar()
    o = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    o.addheaders = [("User-Agent", UA), ("Accept-Language", "fr-FR,fr;q=0.9")]
    return o

def get(o, url, ajax=False, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"X-Requested-With": "XMLHttpRequest"} if ajax else {})
            with o.open(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code < 500 or k >= 1: return ""
            time.sleep(2)
        except Exception as e:
            time.sleep(2 + 3 * k)
    return ""

def txt(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()

def parse(chunk):
    out = []
    for li in re.split(r"<li data-id-offre=", chunk)[1:]:
        m = re.match(r"['\"]([0-9A-Z]+)['\"]", li)
        if not m: continue
        oid = m.group(1)
        title = txt((re.search(r"media-heading-title['\"]>(.*?)</span>", li, re.S) or [None, ""])[1])
        subraw = (re.search(r"class=['\"]subtext['\"]>(.*?)</p>", li, re.S) or [None, ""])[1]
        sp = re.search(r"<span>(.*?)</span>", subraw, re.S)
        if sp:
            ent0 = txt(subraw[:sp.start()]).strip(" -")
            sub = (ent0 + " - " if ent0 else "- ") + txt(sp.group(1))
        else:
            sub = txt(subraw)
        desc = txt((re.search(r"class=['\"]description['\"]>(.*?)</p>", li, re.S) or [None, ""])[1])
        contrat = txt((re.search(r"class=['\"]contrat visible-xs['\"]>(.*?)</p>", li, re.S) or [None, ""])[1])
        date = txt((re.search(r"class=['\"]date['\"]>(.*?)</p>", li, re.S) or [None, ""])[1])
        origine = (re.search(r"alt=['\"]Origine de l(?:'|&#39;)offre : ([^'\"&]+)", li) or [None, ""])[1]
        if sp:
            ent, lieu = (ent0, txt(sp.group(1)))
        elif " - " in sub:
            ent, lieu = sub.split(" - ", 1)
        else:
            ent, lieu = "", sub
        o = dict(id=oid, titre=title, entreprise=ent.strip(" -"), lieu=lieu.strip(), extrait=desc,
                 contrat=contrat, publie=date.replace("Publié ", ""), source=origine)
        if EXCLU.search(title + " " + contrat) or re.search(r"^(en |contrat d.)?(alternance|apprentissage)|recherch\w* (un|une|des) (alternant|apprenti)", desc, re.I): continue
        out.append(o)
    return out

def search(o, params, n, contrats="CDI,CDD,MIS"):
    q = urllib.parse.urlencode(dict(params, typeContrat=contrats, tri="1", offresPartenaires="true"), safe=",")
    page = get(o, f"{BASE}/offres/recherche?{q}")
    offres = parse(page)
    total = re.search(r"([\d\s ]+) offres", page)
    start = 20
    while len(offres) < n and start < 1000 and 'afficherplusderesultats' in page:
        time.sleep(1)
        js = get(o, f"{BASE}/offres/recherche.rechercheoffre:afficherplusderesultats/{start}-{start+19}/1?{q}", ajax=True)
        try:
            chunk = "".join(c[1] for c in json.loads(js)["_tapestry"]["content"])
        except Exception:
            break
        got = parse(chunk)
        if not got and "data-id-offre" not in chunk: break
        offres += got
        start += 20
    return offres[:n]

def contact(o, oid):
    js = get(o, f"{BASE}/offres/recherche/detail.detailstandalone.postuler.contact:chargercontact?t:ac={oid}", ajax=True)
    try:
        h = "".join(c[1] for c in json.loads(js)["_tapestry"]["content"])
    except Exception:
        return {}
    c = {}
    site = re.search(r"href=['\"](https?://(?!candidat\.francetravail)[^'\"]+)['\"]", h)
    if site: c["site"] = html.unescape(site.group(1))
    mail = re.search(r"mailto:([^'\"?]+)", h) or re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", txt(h))
    if mail: c["email"] = mail.group(1) if mail.re.pattern.startswith("mailto") else mail.group(0)
    tel = re.search(r"(?:tel:|Téléphone[^0-9+]*)(\+?[\d .]{9,17})", h)
    if tel: c["tel"] = tel.group(1).strip()
    nom = re.search(r"dropdown-apply-title['\"]>([^<]+)<", h)
    if nom: c["mode"] = txt(nom.group(1))
    if "Se connecter" in h and not c.get("site"): c["connexion"] = True
    return c

def salaire(o, oid):
    h = get(o, f"{BASE}/offres/recherche/detail/{oid}")
    m = re.search(r'<meta content="([^"]*)" name="description"', h)
    if not m: return {}
    d = html.unescape(m.group(1))
    r = {}
    s = re.search(r"Salaire : (Mensuel|Annuel|Horaire) de ([\d.]+) Euros(?: à ([\d.]+) Euros)?", d)
    if s:
        k = {"Mensuel": 12, "Annuel": 1, "Horaire": 1820}[s.group(1)]
        lo = float(s.group(2)) * k; hi = float(s.group(3) or s.group(2)) * k
        if 10000 < lo and hi < 300000:
            r["salMin"] = round(lo); r["salMax"] = round(hi)
            r["salTxt"] = (f"{round(lo/1000)} k€" if round(lo/1000) == round(hi/1000) else f"{round(lo/1000)}–{round(hi/1000)} k€") + " brut/an"
    if re.search(r"t[ée]l[ée]travail", d, re.I): r["tt"] = True
    return r

def main():
    a = sys.argv[1:]
    out = a[0]
    rech = json.load(open(a[1])) if len(a) > 1 and not a[1].startswith("--") else []
    per_dept = int(a[a.index("--par-dept") + 1]) if "--par-dept" in a else 40
    per_rech = int(a[a.index("--par-recherche") + 1]) if "--par-recherche" in a else 100
    depts = a[a.index("--depts") + 1].split(",") if "--depts" in a else DEPTS
    seen, offres, cibles = set(), [], []
    import threading, concurrent.futures
    lock = threading.Lock()
    CFARE = re.compile(r"\bcfa\b|centre de formation|organisme de formation|[ée]cole|formation|p[ée]dagog|campus|des [ée]tudes|apprentissage|qualiopi|examens", re.I)
    ELEC = re.compile(r"\bCFO\b|courants?|[ée]lectri", re.I)
    def one(r):
        mots, dept = (r.get("mots") or "").strip(), (r.get("dept") or "").strip()
        if not mots and not dept: return []
        p = {"emission": str(r.get("jours") or 3)}
        if mots: p["motsCles"] = mots
        if dept: p["lieux"] = "99138" if dept == "MC" else dept + "D"
        o = opener()
        res = search(o, p, int(r.get("max") or per_rech), r.get("contrats") or "CDI,CDD,MIS")
        got = []
        for x in res:
            if r.get("piste") == "cfa" and ELEC.search(x["titre"]): continue
            x["recherche"] = f"{mots}|{dept}"
            x["dept"] = dept
            if r.get("piste"): x["piste"] = "cfa" if CFARE.search(x["titre"]) and not ELEC.search(x["titre"]) else "dg"
            if r.get("contrats") and "LIB" in r["contrats"] or FREE.search(x["titre"] + " " + x["extrait"] + " " + x["contrat"]): x["free"] = True
            if re.search(r"t[ée]l[ée]\s?travail", mots, re.I): x["tt"] = True
            with lock:
                if x["id"] in seen: continue
                seen.add(x["id"])
            time.sleep(0.6)
            x["contact"] = contact(o, x["id"])
            if r.get("salaire"):
                time.sleep(0.6); x.update(salaire(o, x["id"]))
            got.append(x)
        print(f"recherche {mots!r} {dept}: {len(res)}", file=sys.stderr, flush=True)
        return got
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 3
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        for got in ex.map(one, rech):
            cibles.extend(got)
    for d in depts:
        o = opener()
        res = search(o, {"lieux": d + "D", "emission": "1"}, per_dept)
        for x in res:
            if x["id"] not in seen:
                x["dept"] = d; seen.add(x["id"]); offres.append(x)
        print(f"dept {d}: {len(res)}", file=sys.stderr)
        time.sleep(1)
    for x in cibles:
        if x.get("dept"): continue
        m = re.match(r"(\d{2,3}|2A|2B)\s*-", x["lieu"]); x["dept"] = m.group(1) if m else ""
    data = {"maj": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
            "ciblees": cibles, "offres": offres}
    with open(out, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"OK {len(cibles)} ciblées, {len(offres)} générales", file=sys.stderr)

if __name__ == "__main__":
    main()
