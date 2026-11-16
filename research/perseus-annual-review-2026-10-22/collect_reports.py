"""Read-only public report collection and text extraction for this research session."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
RECENT = {
    2005: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2005/RNS/46513_rns_2005-10-26_5b36812d-a4fb-4d39-a53d-799c70c12513.pdf',
    2007: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2007/RNS/46513_rns_2007-10-30_6173c0a3-aa94-462f-862f-08e4202c6294.pdf',
    2008: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2008/RNS/46513_rns_2008-10-28_e289ba5f-38b4-4a0e-913b-e1f559490751.pdf',
    2009: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2009/RNS/46513_rns_2009-10-25_433d2738-7aaf-49fb-97e1-b62994b4234d.pdf',
    2010: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2010/RNS/46513_rns_2010-10-25_df75d41a-f8e6-400a-9791-c9d81016a4b2.pdf',
    2011: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2011/RNS/46513_rns_2011-10-23_625cffd1-58da-4eb9-b279-5cf1e0da958e.pdf',
    2012: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2012/RNS/46513_rns_2012-10-09_cefbfe00-ece6-4310-93d1-0f3adaa9acfb.pdf',
    2013: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2013/RNS/46513_rns_2013-10-13_60cd262d-fb5b-4626-b421-01aeb389827e.pdf',
    2014: 'https://cdn.financialreports.eu/financialreports/media/filings/46513/2014/RNS/46513_rns_2014-10-16_20832cbf-3a89-48d8-a311-9ff223871c0e.pdf',
    2015: 'https://announcements.asx.com.au/asxpdf/20151019/pdf/4325ptj0z0km57.pdf',
    2017: 'https://perseusmining.com/wp-content/uploads/2019/06/PRU-AR-1.pdf',
    2016: 'https://perseusmining.com/wp-content/uploads/2019/06/2016-annual-report.pdf',
    2026: 'https://perseusmining.com/wp-content/uploads/2026/08/Annual-Report-2026.pdf',
    2025: 'https://perseusmining.com/wp-content/uploads/2025/08/Perseus-2025-Annual-Report-Final.pdf',
    2024: 'https://perseusmining.com/wp-content/uploads/2024/08/Annual-Report-2024.pdf',
    2023: 'https://perseusmining.com/wp-content/uploads/2023/09/Annual-Report-2023.pdf',
    2022: 'https://perseusmining.com/wp-content/uploads/2022/10/Perseus_2022-Annual-Report.pdf',
    2021: 'https://perseusmining.com/wp-content/uploads/2021/10/Annual-Report-to-shareholders-3.pdf',
    2020: 'https://perseusmining.com/wp-content/uploads/2020/10/02295393-1.pdf',
    2019: 'https://perseusmining.com/wp-content/uploads/2019/10/02161808.pdf',
    2018: 'https://perseusmining.com/wp-content/uploads/2019/06/02034526.pdf',
}

def collect(year):
    url = RECENT.get(year, f'https://www.annualreports.com/HostedData/AnnualReportArchive/P/ASX_PRU_{year}.pdf')
    out = ROOT / 'sources' / f'Perseus-{year}.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        data = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
        if not data.startswith(b'%PDF'):
            raise ValueError(f'Not PDF: {url}')
        out.write_bytes(data)
    data = out.read_bytes()
    reader = PdfReader(out)
    pages = [{'pdf_page': i+1, 'text': page.extract_text() or ''} for i,page in enumerate(reader.pages)]
    (ROOT/'text').mkdir(exist_ok=True)
    (ROOT/'text'/f'{year}.json').write_text(json.dumps(pages, ensure_ascii=False))
    (ROOT/'text'/f'{year}.txt').write_text('\n\n'.join(f'=== PDF PAGE {p["pdf_page"]} ===\n{p["text"]}' for p in pages))
    return {'year':year, 'url':url, 'pdf':str(out.relative_to(ROOT)), 'pages':len(pages), 'text_characters':sum(len(p['text']) for p in pages), 'sha256':hashlib.sha256(data).hexdigest(), 'first_page_excerpt':pages[0]['text'][:250]}

if __name__ == '__main__':
    manifest=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(collect,y):y for y in range(2004,2027)}
        for f in concurrent.futures.as_completed(futures):
            year=futures[f]
            try:
                result=f.result(); manifest.append(result)
                print(json.dumps({k:result[k] for k in ['year','pages','text_characters','first_page_excerpt']}),flush=True)
            except Exception as e:
                manifest.append({'year':year,'error':str(e)});print(year,type(e).__name__,str(e),flush=True)
    (ROOT/'manifest.json').write_text(json.dumps(sorted(manifest,key=lambda x:x['year']),indent=2))
