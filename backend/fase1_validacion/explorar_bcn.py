import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Probar BCN con boletín de desalinización
urls = [
    "https://www.bcn.cl/historiadelaley/nc/historia-de-la-ley/8406/",
    "https://leychile.cl/Navegar?idNorma=1208435",
    "https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin=11608-09",
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getProyectosDeLey?prmBoletin=11608-09",
]

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"\nURL: {url}")
        print(f"HTTP: {r.status_code} | {len(r.content)} bytes")
        if r.status_code == 200 and len(r.content) > 5000:
            soup = BeautifulSoup(r.content, "html.parser")
            for tag in soup.find_all(["script","style"]):
                tag.decompose()
            texto = soup.get_text(separator="\n", strip=True)
            lineas = [l for l in texto.split("\n") if len(l) > 20]
            print(f"Líneas útiles: {len(lineas)}")
            for l in lineas[:15]:
                print(f"  {l}")
    except Exception as e:
        print(f"  Error: {e}")

# Probar el endpoint XML del Senado con boletín específico
print("\n\nEndpoint XML Senado con boletín:")
url_xml = "https://tramitacion.senado.cl/wspublico/tramitacion.php?boletin=11608-09"
r = requests.get(url_xml, headers=HEADERS, timeout=15)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")
print(f"Primeros 500 chars:\n{r.text[:500]}")
