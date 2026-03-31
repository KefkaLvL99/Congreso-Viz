import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Ver el WSDL para saber qué métodos existen
urls = [
    "https://opendata.congreso.cl/wscamaradiputados.asmx?WSDL",
    "https://opendata.congreso.cl/wscamaradiputados.asmx",
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getVotacionesDeUnProyecto?prmBoletin=11608-09",
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getVotacionesDeSala?prmAnno=2025",
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getVotacionesDeSalaXAnno?prmAnno=2025",
]

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        print(f"  Primeros 500 chars: {r.text[:500]}")
    except Exception as e:
        print(f"\n{url} → Error: {e}")
