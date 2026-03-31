# Buscar votación con votos No y Abstención para ver estructura completa
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Buscar una votación con No y Abstención — el kerosene fue 133-0-0
# Probemos con IDs anteriores hasta encontrar una con votos No
for vid in range(88490, 88500):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if len(r.content) < 60000:
        continue

    soup = BeautifulSoup(r.content, "html.parser")

    # Buscar conteos
    tablas = soup.find_all("table")
    if not tablas:
        continue

    celdas = [td.get_text(strip=True) for td in tablas[0].find_all("td")]
    nums = [c for c in celdas if c.isdigit()]
    if len(nums) >= 4 and (int(nums[1]) > 0 or int(nums[2]) > 0):
        print(f"\n✅ ID {vid} tiene votos No/Abstención: Si={nums[0]} No={nums[1]} Abs={nums[2]}")
        print(f"   Tablas encontradas: {len(tablas)}")

        for i, tabla in enumerate(tablas):
            filas = tabla.find_all("tr")
            print(f"\n   Tabla {i+1}: {len(filas)} filas")
            # Buscar encabezado o título de la tabla
            caption = tabla.find("caption")
            if caption:
                print(f"   Caption: {caption.get_text(strip=True)}")
            # Mostrar primeras filas
            for fila in filas[:4]:
                cds = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
                if any(c for c in cds):
                    print(f"     {cds}")

        # Buscar divs con listas de votos
        for div in soup.find_all("div", class_=True):
            clase = " ".join(div.get("class", []))
            texto = div.get_text(strip=True)
            if any(k in clase for k in ["voto", "vote", "resultado", "diputado"]):
                print(f"\n   DIV .{clase}: {texto[:100]}")

        # Mostrar texto limpio alrededor de "No" y "Abstención"
        for tag in soup.find_all(["script","style"]):
            tag.decompose()
        texto_completo = soup.get_text(separator="\n", strip=True)
        lineas = texto_completo.split("\n")
        for i, linea in enumerate(lineas):
            if any(k in linea for k in ["Abstención", "Abstencion", "En contra", "No votó"]):
                print(f"\n   Contexto línea {i}: {lineas[max(0,i-2):i+5]}")
        break
