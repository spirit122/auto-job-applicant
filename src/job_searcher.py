#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
BUSCADOR DE TRABAJOS - UNREAL ENGINE / GAME DEVELOPER
===============================================================================

Autor: spirit122
Descripcion: Busca ofertas de trabajo relacionadas con Unreal Engine y
             desarrollo de videojuegos desde multiples fuentes publicas,
             filtra por palabras clave y ubicacion, genera un reporte HTML
             y lo envia por correo electronico.

===============================================================================
INSTRUCCIONES DE CONFIGURACION - GMAIL APP PASSWORD
===============================================================================

Para enviar correos con Gmail necesitas crear una "Contrasena de aplicacion":

1. Ve a https://myaccount.google.com/security
2. Asegurate de tener la "Verificacion en 2 pasos" ACTIVADA
   (si no la tienes, activala primero)
3. Ve a https://myaccount.google.com/apppasswords
4. En "Seleccionar app" elige "Correo"
5. En "Seleccionar dispositivo" elige "Otro" y escribe "BuscadorTrabajos"
6. Haz clic en "Generar"
7. Google te mostrara una contrasena de 16 caracteres (ejemplo: abcd efgh ijkl mnop)
8. Copia esa contrasena SIN espacios y pegala en la variable GMAIL_APP_PASSWORD
   de este script (linea ~90), o mejor aun, en la variable de entorno
   GMAIL_APP_PASSWORD de tu sistema.

IMPORTANTE: NO uses tu contrasena normal de Gmail. Usa SOLO la contrasena
            de aplicacion generada en el paso anterior.

Para configurar la variable de entorno en Windows (recomendado):
   - Abre CMD como administrador
   - Ejecuta: setx GMAIL_APP_PASSWORD "tucontrasenaaqui"
   - Reinicia la terminal

===============================================================================
DEPENDENCIAS - Instalar antes de ejecutar
===============================================================================

   pip install requests beautifulsoup4 feedparser lxml

===============================================================================
"""

import os
import sys
import json
import time
import logging
import smtplib
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote_plus, urlencode
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

# =====================================================================
# Intentar importar dependencias externas con mensajes claros de error
# =====================================================================
try:
    import requests
except ImportError:
    print("ERROR: Falta la libreria 'requests'. Instala con: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Falta la libreria 'beautifulsoup4'. Instala con: pip install beautifulsoup4")
    sys.exit(1)

try:
    import feedparser
except ImportError:
    print("ERROR: Falta la libreria 'feedparser'. Instala con: pip install feedparser")
    sys.exit(1)


# =====================================================================
# CONFIGURACION PRINCIPAL - EDITAR SEGUN TUS NECESIDADES
# =====================================================================

# --- Correo electronico ---
GMAIL_REMITENTE = os.environ.get("GMAIL_REMITENTE", "your@gmail.com")
GMAIL_DESTINATARIO = os.environ.get("GMAIL_DESTINATARIO", "your@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")  # Contrasena de app (ver instrucciones arriba)

# --- Palabras clave de busqueda ---
# El script buscara trabajos que contengan CUALQUIERA de estas palabras
PALABRAS_CLAVE = [
    "Unreal Engine",
    "Game Developer",
    "UE5",
    "UE4",
    "Blueprint",
    "Game Programmer",
    "Technical Artist",
    "Environment Artist",
    "Oceanology",
    "Gameplay Programmer",
    "Level Designer",
    "Game Designer",
    "Unreal Developer",
]

# --- Ubicaciones deseadas ---
# El script filtrara resultados que mencionen estas ubicaciones
UBICACIONES = [
    "Chile",
    "Remote",
    "Remoto",
    "Latin America",
    "LATAM",
    "Latinoamerica",
    "Latinoamérica",
    "América Latina",
    "South America",
    "Sudamérica",
    # Add your city here (e.g., "New York", "London", "Berlin")
    "Worldwide",
    "Anywhere",
    "Global",
]

# --- Configuracion de archivos de salida ---
DIRECTORIO_SALIDA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_HTML = os.path.join(DIRECTORIO_SALIDA, "resultados_trabajos.html")
ARCHIVO_LOG = os.path.join(DIRECTORIO_SALIDA, "job_searcher.log")
ARCHIVO_CACHE = os.path.join(DIRECTORIO_SALIDA, "trabajos_cache.json")

# --- Configuracion de busqueda ---
DIAS_MAXIMOS = 30          # Solo mostrar trabajos de los ultimos N dias
TIMEOUT_REQUESTS = 20      # Tiempo maximo de espera por request (segundos)
PAUSA_ENTRE_REQUESTS = 2   # Pausa entre requests para no saturar servidores


# =====================================================================
# CONFIGURACION DE LOGGING (registro de eventos)
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(ARCHIVO_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =====================================================================
# MODELO DE DATOS - Estructura de cada oferta de trabajo
# =====================================================================
@dataclass
class OfertaTrabajo:
    """Representa una oferta de trabajo encontrada."""
    titulo: str = ""
    empresa: str = ""
    ubicacion: str = ""
    salario: str = "No especificado"
    enlace: str = ""
    fecha_publicacion: str = ""
    fuente: str = ""
    descripcion: str = ""

    def identificador_unico(self) -> str:
        """Genera un hash unico para evitar duplicados."""
        texto = f"{self.titulo.lower().strip()}{self.empresa.lower().strip()}"
        return hashlib.md5(texto.encode("utf-8")).hexdigest()


# =====================================================================
# FUNCIONES AUXILIARES
# =====================================================================

def crear_sesion_http() -> requests.Session:
    """
    Crea una sesion HTTP con headers realistas para evitar bloqueos.
    Algunos sitios bloquean requests sin User-Agent adecuado.
    """
    sesion = requests.Session()
    sesion.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return sesion


def contiene_palabra_clave(texto: str, palabras: List[str]) -> bool:
    """
    Verifica si el texto contiene alguna de las palabras clave.
    La comparacion es insensible a mayusculas/minusculas.
    """
    texto_lower = texto.lower()
    return any(palabra.lower() in texto_lower for palabra in palabras)


def coincide_ubicacion(texto_ubicacion: str, ubicaciones: List[str]) -> bool:
    """
    Verifica si la ubicacion del trabajo coincide con las ubicaciones deseadas.
    Si la ubicacion esta vacia, se considera como posible match (se incluye).
    """
    if not texto_ubicacion or texto_ubicacion.strip() == "":
        return True  # Si no hay ubicacion, incluir por las dudas
    texto_lower = texto_ubicacion.lower()
    return any(ub.lower() in texto_lower for ub in ubicaciones)


def limpiar_texto(texto: str) -> str:
    """Limpia texto HTML y caracteres especiales."""
    if not texto:
        return ""
    # Remover tags HTML si los hay
    soup = BeautifulSoup(texto, "html.parser")
    limpio = soup.get_text(separator=" ", strip=True)
    # Remover multiples espacios
    limpio = " ".join(limpio.split())
    return limpio.strip()


def formatear_fecha(fecha_str: str) -> str:
    """Intenta formatear una fecha a formato legible."""
    if not fecha_str:
        return "Sin fecha"
    # Intentar varios formatos comunes
    formatos = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",
    ]
    for fmt in formatos:
        try:
            dt = datetime.strptime(fecha_str.strip(), fmt)
            return dt.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            continue
    return fecha_str[:10] if len(fecha_str) > 10 else fecha_str


# =====================================================================
# FUENTES DE BUSQUEDA - Cada funcion busca en un sitio diferente
# =====================================================================

def buscar_remoteok(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en RemoteOK.com usando su API publica.
    RemoteOK es una bolsa de trabajo enfocada en trabajos remotos.
    API: https://remoteok.com/api
    """
    logger.info("Buscando en RemoteOK...")
    ofertas = []

    try:
        # La API de RemoteOK devuelve JSON directamente
        url = "https://remoteok.com/api"
        respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)
        respuesta.raise_for_status()

        datos = respuesta.json()

        # El primer elemento es metadata, lo saltamos
        for item in datos[1:]:
            titulo = item.get("position", "")
            empresa = item.get("company", "")
            ubicacion = item.get("location", "Remote")
            descripcion = limpiar_texto(item.get("description", ""))
            enlace = item.get("url", "")
            fecha = item.get("date", "")
            salario_min = item.get("salary_min", "")
            salario_max = item.get("salary_max", "")
            tags = " ".join(item.get("tags", []))

            # Construir string de salario si hay datos
            salario = "No especificado"
            if salario_min and salario_max:
                salario = f"${salario_min:,} - ${salario_max:,} USD"
            elif salario_min:
                salario = f"Desde ${salario_min:,} USD"
            elif salario_max:
                salario = f"Hasta ${salario_max:,} USD"

            # Verificar si coincide con nuestras palabras clave
            texto_completo = f"{titulo} {empresa} {descripcion} {tags}"
            if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                if coincide_ubicacion(ubicacion, UBICACIONES):
                    ofertas.append(OfertaTrabajo(
                        titulo=limpiar_texto(titulo),
                        empresa=limpiar_texto(empresa),
                        ubicacion=ubicacion if ubicacion else "Remote",
                        salario=salario,
                        enlace=enlace if enlace.startswith("http") else f"https://remoteok.com{enlace}",
                        fecha_publicacion=formatear_fecha(fecha),
                        fuente="RemoteOK",
                        descripcion=descripcion[:200],
                    ))

        logger.info(f"RemoteOK: Se encontraron {len(ofertas)} ofertas relevantes")

    except requests.exceptions.Timeout:
        logger.warning("RemoteOK: Tiempo de espera agotado")
    except requests.exceptions.RequestException as e:
        logger.error(f"RemoteOK: Error de conexion - {e}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"RemoteOK: Error al procesar datos - {e}")

    return ofertas


def buscar_indeed_rss(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en Indeed usando feeds RSS publicos.
    Indeed ofrece feeds RSS para busquedas de empleo.
    Nota: La disponibilidad de los RSS de Indeed puede variar por region.
    """
    logger.info("Buscando en Indeed RSS...")
    ofertas = []

    # Construir varias consultas de busqueda
    consultas = [
        ("Unreal Engine", "Remote"),
        ("Game Developer", "Remote"),
        ("Unreal Engine", "Chile"),
        ("Game Developer", "Chile"),
        ("UE5 Developer", "Remote"),
        ("Game Programmer", "Remote"),
        ("Technical Artist Unreal", "Remote"),
        ("Environment Artist", "Remote"),
    ]

    for query, location in consultas:
        try:
            # URL del feed RSS de Indeed
            params = {
                "q": query,
                "l": location,
                "sort": "date",
                "fromage": str(DIAS_MAXIMOS),
            }
            url = f"https://www.indeed.com/rss?{urlencode(params)}"

            logger.info(f"  Indeed RSS: Buscando '{query}' en '{location}'...")
            respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)

            if respuesta.status_code == 200:
                # Parsear el feed RSS con feedparser
                feed = feedparser.parse(respuesta.content)

                for entrada in feed.entries:
                    titulo = limpiar_texto(getattr(entrada, "title", ""))
                    enlace = getattr(entrada, "link", "")
                    fecha = getattr(entrada, "published", "")
                    descripcion = limpiar_texto(getattr(entrada, "summary", ""))

                    # Extraer empresa y ubicacion del titulo si es posible
                    # Indeed suele poner el formato: "Titulo - Empresa - Ubicacion"
                    empresa = ""
                    ubicacion_oferta = location
                    if " - " in titulo:
                        partes = titulo.split(" - ")
                        if len(partes) >= 3:
                            titulo = partes[0].strip()
                            empresa = partes[1].strip()
                            ubicacion_oferta = partes[2].strip()
                        elif len(partes) == 2:
                            titulo = partes[0].strip()
                            empresa = partes[1].strip()

                    texto_completo = f"{titulo} {empresa} {descripcion}"
                    if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                        ofertas.append(OfertaTrabajo(
                            titulo=titulo,
                            empresa=empresa,
                            ubicacion=ubicacion_oferta,
                            salario="No especificado",
                            enlace=enlace,
                            fecha_publicacion=formatear_fecha(fecha),
                            fuente="Indeed",
                            descripcion=descripcion[:200],
                        ))

            time.sleep(PAUSA_ENTRE_REQUESTS)

        except requests.exceptions.Timeout:
            logger.warning(f"Indeed RSS: Tiempo de espera agotado para '{query}'")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Indeed RSS: Error de conexion para '{query}' - {e}")
        except Exception as e:
            logger.warning(f"Indeed RSS: Error inesperado para '{query}' - {e}")

    logger.info(f"Indeed RSS: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


def buscar_linkedin_publico(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en LinkedIn usando la pagina publica de empleos.
    Nota: LinkedIn puede limitar el acceso automatizado. Esta funcion
    intenta extraer datos de la pagina publica de busqueda de empleo.
    """
    logger.info("Buscando en LinkedIn (pagina publica)...")
    ofertas = []

    consultas = [
        "Unreal Engine Remote",
        "Game Developer Remote Latin America",
        "UE5 Developer Remote",
        "Game Developer Chile",
        "Technical Artist Unreal Remote",
        "Unreal Engine LATAM",
    ]

    for query in consultas:
        try:
            # URL publica de busqueda de empleo en LinkedIn
            params = {
                "keywords": query,
                "location": "Worldwide",
                "f_TPR": "r2592000",  # Ultimo mes
                "f_WT": "2",          # Trabajo remoto
            }
            url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"

            logger.info(f"  LinkedIn: Buscando '{query}'...")
            respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)

            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.text, "html.parser")

                # LinkedIn usa diferentes selectores segun la version de la pagina
                # Intentar multiples selectores conocidos
                tarjetas = soup.find_all("div", class_="base-card")
                if not tarjetas:
                    tarjetas = soup.find_all("li", class_="result-card")
                if not tarjetas:
                    tarjetas = soup.find_all("div", class_="job-search-card")

                for tarjeta in tarjetas:
                    try:
                        # Extraer titulo
                        elem_titulo = (
                            tarjeta.find("h3", class_="base-search-card__title")
                            or tarjeta.find("span", class_="screen-reader-text")
                            or tarjeta.find("h3")
                        )
                        titulo = limpiar_texto(elem_titulo.get_text()) if elem_titulo else ""

                        # Extraer empresa
                        elem_empresa = (
                            tarjeta.find("h4", class_="base-search-card__subtitle")
                            or tarjeta.find("a", class_="hidden-nested-link")
                        )
                        empresa = limpiar_texto(elem_empresa.get_text()) if elem_empresa else ""

                        # Extraer ubicacion
                        elem_ubicacion = tarjeta.find("span", class_="job-search-card__location")
                        ubicacion = limpiar_texto(elem_ubicacion.get_text()) if elem_ubicacion else ""

                        # Extraer enlace
                        elem_enlace = tarjeta.find("a", class_="base-card__full-link") or tarjeta.find("a")
                        enlace = elem_enlace.get("href", "") if elem_enlace else ""

                        # Extraer fecha
                        elem_fecha = tarjeta.find("time")
                        fecha = elem_fecha.get("datetime", "") if elem_fecha else ""

                        if titulo:
                            texto_completo = f"{titulo} {empresa} {ubicacion}"
                            if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                                if coincide_ubicacion(ubicacion, UBICACIONES):
                                    ofertas.append(OfertaTrabajo(
                                        titulo=titulo,
                                        empresa=empresa,
                                        ubicacion=ubicacion if ubicacion else "Ver enlace",
                                        salario="No especificado",
                                        enlace=enlace,
                                        fecha_publicacion=formatear_fecha(fecha),
                                        fuente="LinkedIn",
                                    ))
                    except Exception as e:
                        logger.debug(f"LinkedIn: Error al procesar tarjeta - {e}")
                        continue

            time.sleep(PAUSA_ENTRE_REQUESTS)

        except requests.exceptions.Timeout:
            logger.warning(f"LinkedIn: Tiempo de espera agotado para '{query}'")
        except requests.exceptions.RequestException as e:
            logger.warning(f"LinkedIn: Error de conexion para '{query}' - {e}")
        except Exception as e:
            logger.warning(f"LinkedIn: Error inesperado para '{query}' - {e}")

    logger.info(f"LinkedIn: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


def buscar_gamedevjobs(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en GameJobs.co - Bolsa de trabajo especializada
    en la industria de videojuegos.
    """
    logger.info("Buscando en GameJobs.co...")
    ofertas = []

    consultas = [
        "unreal-engine",
        "game-developer",
        "technical-artist",
        "environment-artist",
        "game-programmer",
    ]

    for query in consultas:
        try:
            url = f"https://gamejobs.co/search?q={quote_plus(query)}"
            logger.info(f"  GameJobs: Buscando '{query}'...")
            respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)

            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.text, "html.parser")

                # Buscar tarjetas de trabajo
                tarjetas = soup.find_all("a", class_="job-listing")
                if not tarjetas:
                    tarjetas = soup.find_all("div", class_="job-card")
                if not tarjetas:
                    # Busqueda generica de enlaces que parezcan ofertas
                    tarjetas = soup.find_all("a", href=lambda h: h and "/job/" in h if h else False)

                for tarjeta in tarjetas:
                    try:
                        titulo = ""
                        empresa = ""
                        ubicacion = ""

                        # Intentar extraer datos segun la estructura del sitio
                        elem_titulo = tarjeta.find("h2") or tarjeta.find("h3") or tarjeta.find("strong")
                        if elem_titulo:
                            titulo = limpiar_texto(elem_titulo.get_text())
                        elif isinstance(tarjeta, dict):
                            titulo = limpiar_texto(tarjeta.get_text())

                        elem_empresa = tarjeta.find("span", class_="company") or tarjeta.find("p")
                        if elem_empresa:
                            empresa = limpiar_texto(elem_empresa.get_text())

                        elem_ubicacion = tarjeta.find("span", class_="location")
                        if elem_ubicacion:
                            ubicacion = limpiar_texto(elem_ubicacion.get_text())

                        enlace = tarjeta.get("href", "")
                        if enlace and not enlace.startswith("http"):
                            enlace = f"https://gamejobs.co{enlace}"

                        if titulo and coincide_ubicacion(ubicacion, UBICACIONES):
                            ofertas.append(OfertaTrabajo(
                                titulo=titulo,
                                empresa=empresa,
                                ubicacion=ubicacion if ubicacion else "Ver enlace",
                                salario="No especificado",
                                enlace=enlace,
                                fecha_publicacion="Reciente",
                                fuente="GameJobs.co",
                            ))
                    except Exception as e:
                        logger.debug(f"GameJobs: Error al procesar tarjeta - {e}")
                        continue

            time.sleep(PAUSA_ENTRE_REQUESTS)

        except requests.exceptions.RequestException as e:
            logger.warning(f"GameJobs: Error de conexion para '{query}' - {e}")
        except Exception as e:
            logger.warning(f"GameJobs: Error inesperado para '{query}' - {e}")

    logger.info(f"GameJobs: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


def buscar_hitmarker(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en Hitmarker.net - Plataforma de empleos para
    la industria de videojuegos y esports.
    """
    logger.info("Buscando en Hitmarker...")
    ofertas = []

    consultas = [
        "unreal engine",
        "game developer",
        "ue5",
        "technical artist",
    ]

    for query in consultas:
        try:
            url = f"https://hitmarker.net/jobs?q={quote_plus(query)}&remote=true"
            logger.info(f"  Hitmarker: Buscando '{query}'...")
            respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)

            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.text, "html.parser")

                tarjetas = soup.find_all("a", class_="job-card")
                if not tarjetas:
                    tarjetas = soup.find_all("div", class_="job-listing")
                if not tarjetas:
                    tarjetas = soup.find_all("article")

                for tarjeta in tarjetas:
                    try:
                        elem_titulo = tarjeta.find("h2") or tarjeta.find("h3")
                        titulo = limpiar_texto(elem_titulo.get_text()) if elem_titulo else ""

                        elem_empresa = tarjeta.find("span", class_="company")
                        empresa = limpiar_texto(elem_empresa.get_text()) if elem_empresa else ""

                        elem_ubicacion = tarjeta.find("span", class_="location")
                        ubicacion = limpiar_texto(elem_ubicacion.get_text()) if elem_ubicacion else "Remote"

                        enlace = tarjeta.get("href", "")
                        if enlace and not enlace.startswith("http"):
                            enlace = f"https://hitmarker.net{enlace}"

                        if titulo:
                            texto_completo = f"{titulo} {empresa}"
                            if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                                if coincide_ubicacion(ubicacion, UBICACIONES):
                                    ofertas.append(OfertaTrabajo(
                                        titulo=titulo,
                                        empresa=empresa,
                                        ubicacion=ubicacion,
                                        salario="No especificado",
                                        enlace=enlace,
                                        fecha_publicacion="Reciente",
                                        fuente="Hitmarker",
                                    ))
                    except Exception as e:
                        logger.debug(f"Hitmarker: Error al procesar tarjeta - {e}")
                        continue

            time.sleep(PAUSA_ENTRE_REQUESTS)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Hitmarker: Error de conexion para '{query}' - {e}")
        except Exception as e:
            logger.warning(f"Hitmarker: Error inesperado para '{query}' - {e}")

    logger.info(f"Hitmarker: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


def buscar_workingnomads(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en Working Nomads - Plataforma de trabajos remotos
    que tiene una API JSON publica.
    """
    logger.info("Buscando en Working Nomads...")
    ofertas = []

    try:
        url = "https://www.workingnomads.com/api/exposed_jobs/"
        respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)
        respuesta.raise_for_status()

        datos = respuesta.json()

        for item in datos:
            titulo = item.get("title", "")
            empresa = item.get("company_name", "")
            ubicacion = item.get("location", "Remote")
            descripcion = limpiar_texto(item.get("description", ""))
            enlace = item.get("url", "")
            fecha = item.get("pub_date", "")
            categoria = item.get("category_name", "")

            texto_completo = f"{titulo} {empresa} {descripcion} {categoria}"
            if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                if coincide_ubicacion(ubicacion, UBICACIONES):
                    ofertas.append(OfertaTrabajo(
                        titulo=limpiar_texto(titulo),
                        empresa=limpiar_texto(empresa),
                        ubicacion=ubicacion if ubicacion else "Remote",
                        salario="No especificado",
                        enlace=enlace,
                        fecha_publicacion=formatear_fecha(fecha),
                        fuente="Working Nomads",
                        descripcion=descripcion[:200],
                    ))

    except requests.exceptions.RequestException as e:
        logger.warning(f"Working Nomads: Error de conexion - {e}")
    except Exception as e:
        logger.warning(f"Working Nomads: Error inesperado - {e}")

    logger.info(f"Working Nomads: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


def buscar_remotive(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en Remotive.com usando su API publica.
    Remotive es una plataforma de trabajos remotos con API gratuita.
    """
    logger.info("Buscando en Remotive...")
    ofertas = []

    try:
        # API publica de Remotive
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
        respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)
        respuesta.raise_for_status()

        datos = respuesta.json()
        trabajos = datos.get("jobs", [])

        for item in trabajos:
            titulo = item.get("title", "")
            empresa = item.get("company_name", "")
            ubicacion = item.get("candidate_required_location", "Remote")
            descripcion = limpiar_texto(item.get("description", ""))
            enlace = item.get("url", "")
            fecha = item.get("publication_date", "")
            salario = item.get("salary", "No especificado")
            tags = " ".join(item.get("tags", []))

            texto_completo = f"{titulo} {empresa} {descripcion} {tags}"
            if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                if coincide_ubicacion(ubicacion, UBICACIONES):
                    ofertas.append(OfertaTrabajo(
                        titulo=limpiar_texto(titulo),
                        empresa=limpiar_texto(empresa),
                        ubicacion=ubicacion if ubicacion else "Remote",
                        salario=salario if salario else "No especificado",
                        enlace=enlace,
                        fecha_publicacion=formatear_fecha(fecha),
                        fuente="Remotive",
                        descripcion=descripcion[:200],
                    ))

    except requests.exceptions.RequestException as e:
        logger.warning(f"Remotive: Error de conexion - {e}")
    except Exception as e:
        logger.warning(f"Remotive: Error inesperado - {e}")

    logger.info(f"Remotive: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


def buscar_jooble_rss(sesion: requests.Session) -> List[OfertaTrabajo]:
    """
    Busca trabajos en Jooble usando su feed RSS publico.
    Jooble es un metabuscador de empleo que agrega ofertas de multiples fuentes.
    """
    logger.info("Buscando en Jooble RSS...")
    ofertas = []

    consultas = [
        ("unreal+engine", "remote"),
        ("game+developer", "remote"),
        ("ue5", "remote"),
        ("game+developer", "chile"),
    ]

    for query, location in consultas:
        try:
            url = f"https://jooble.org/rss/{query}/{location}"
            logger.info(f"  Jooble: Buscando '{query}' en '{location}'...")

            respuesta = sesion.get(url, timeout=TIMEOUT_REQUESTS)

            if respuesta.status_code == 200:
                feed = feedparser.parse(respuesta.content)

                for entrada in feed.entries:
                    titulo = limpiar_texto(getattr(entrada, "title", ""))
                    enlace = getattr(entrada, "link", "")
                    fecha = getattr(entrada, "published", "")
                    descripcion = limpiar_texto(getattr(entrada, "summary", ""))

                    # Intentar extraer empresa de la descripcion
                    empresa = ""

                    texto_completo = f"{titulo} {descripcion}"
                    if contiene_palabra_clave(texto_completo, PALABRAS_CLAVE):
                        ofertas.append(OfertaTrabajo(
                            titulo=titulo,
                            empresa=empresa,
                            ubicacion=location.capitalize(),
                            salario="No especificado",
                            enlace=enlace,
                            fecha_publicacion=formatear_fecha(fecha),
                            fuente="Jooble",
                            descripcion=descripcion[:200],
                        ))

            time.sleep(PAUSA_ENTRE_REQUESTS)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Jooble: Error de conexion para '{query}' - {e}")
        except Exception as e:
            logger.warning(f"Jooble: Error inesperado para '{query}' - {e}")

    logger.info(f"Jooble: Se encontraron {len(ofertas)} ofertas relevantes")
    return ofertas


# =====================================================================
# ELIMINACION DE DUPLICADOS
# =====================================================================

def eliminar_duplicados(ofertas: List[OfertaTrabajo]) -> List[OfertaTrabajo]:
    """
    Elimina ofertas duplicadas basandose en un hash del titulo y empresa.
    Mantiene la primera aparicion de cada oferta.
    """
    vistos = set()
    unicas = []
    for oferta in ofertas:
        id_unico = oferta.identificador_unico()
        if id_unico not in vistos:
            vistos.add(id_unico)
            unicas.append(oferta)
    eliminados = len(ofertas) - len(unicas)
    if eliminados > 0:
        logger.info(f"Se eliminaron {eliminados} ofertas duplicadas")
    return unicas


# =====================================================================
# GENERACION DEL REPORTE HTML
# =====================================================================

def generar_html(ofertas: List[OfertaTrabajo], fecha_busqueda: str) -> str:
    """
    Genera un reporte HTML profesional con todas las ofertas encontradas.
    El HTML incluye estilos CSS inline para compatibilidad con clientes de correo.
    """
    total = len(ofertas)

    # Contar ofertas por fuente
    fuentes_conteo = {}
    for o in ofertas:
        fuentes_conteo[o.fuente] = fuentes_conteo.get(o.fuente, 0) + 1
    resumen_fuentes = " | ".join(f"{k}: {v}" for k, v in sorted(fuentes_conteo.items()))

    # Generar filas de la tabla
    filas_html = ""
    for i, oferta in enumerate(ofertas, 1):
        # Alternar colores de fila para mejor legibilidad
        color_fondo = "#f8f9fa" if i % 2 == 0 else "#ffffff"

        # Color segun la fuente
        colores_fuente = {
            "RemoteOK": "#4CAF50",
            "Indeed": "#2164f3",
            "LinkedIn": "#0077B5",
            "GameJobs.co": "#FF6B35",
            "Hitmarker": "#E91E63",
            "Working Nomads": "#9C27B0",
            "Remotive": "#00BCD4",
            "Jooble": "#FF9800",
        }
        color_badge = colores_fuente.get(oferta.fuente, "#607D8B")

        filas_html += f"""
        <tr style="background-color: {color_fondo};">
            <td style="padding: 12px 15px; border-bottom: 1px solid #e0e0e0; font-weight: 600; color: #1a1a2e;">
                {oferta.titulo}
                <br>
                <span style="display: inline-block; padding: 2px 8px; border-radius: 12px;
                       background-color: {color_badge}; color: white; font-size: 11px;
                       font-weight: 500; margin-top: 4px;">
                    {oferta.fuente}
                </span>
            </td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #e0e0e0; color: #333;">
                {oferta.empresa if oferta.empresa else '<span style="color: #999;">No especificada</span>'}
            </td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #e0e0e0; color: #333;">
                {oferta.ubicacion}
            </td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #e0e0e0; color: #2e7d32; font-weight: 500;">
                {oferta.salario}
            </td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #e0e0e0;">
                <a href="{oferta.enlace}" target="_blank"
                   style="display: inline-block; padding: 6px 14px; background-color: #1a73e8;
                          color: white; text-decoration: none; border-radius: 5px;
                          font-size: 13px; font-weight: 500;">
                    Ver oferta
                </a>
            </td>
            <td style="padding: 12px 15px; border-bottom: 1px solid #e0e0e0; color: #666; font-size: 13px;">
                {oferta.fecha_publicacion}
            </td>
        </tr>"""

    # Si no hay ofertas, mostrar mensaje
    if not ofertas:
        filas_html = """
        <tr>
            <td colspan="6" style="padding: 40px; text-align: center; color: #666; font-style: italic;">
                No se encontraron ofertas que coincidan con los criterios de busqueda.<br>
                Intenta ampliar las palabras clave o las ubicaciones en la configuracion del script.
            </td>
        </tr>"""

    # Generar lista de palabras clave y ubicaciones para el reporte
    palabras_badges = " ".join(
        f'<span style="display: inline-block; padding: 3px 10px; margin: 2px; '
        f'border-radius: 15px; background-color: #e3f2fd; color: #1565c0; '
        f'font-size: 12px; border: 1px solid #bbdefb;">{p}</span>'
        for p in PALABRAS_CLAVE
    )
    ubicaciones_badges = " ".join(
        f'<span style="display: inline-block; padding: 3px 10px; margin: 2px; '
        f'border-radius: 15px; background-color: #f3e5f5; color: #7b1fa2; '
        f'font-size: 12px; border: 1px solid #ce93d8;">{u}</span>'
        for u in UBICACIONES[:8]  # Mostrar solo las primeras 8 para no saturar
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultados de Busqueda - Trabajos Unreal Engine / Game Dev</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
             background-color: #f0f2f5; color: #1a1a2e;">

    <!-- Contenedor principal -->
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">

        <!-- Encabezado -->
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                    border-radius: 15px; padding: 30px; margin-bottom: 25px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h1 style="color: #e94560; margin: 0 0 5px 0; font-size: 28px;">
                &#127918; Buscador de Trabajos - Game Dev & Unreal Engine
            </h1>
            <p style="color: #a8a8b3; margin: 0; font-size: 14px;">
                Busqueda automatizada de ofertas de empleo | Generado el {fecha_busqueda}
            </p>
        </div>

        <!-- Resumen -->
        <div style="background-color: #ffffff; border-radius: 12px; padding: 20px;
                    margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">
                <div style="background: linear-gradient(135deg, #e94560, #c62a45); border-radius: 10px;
                            padding: 15px 25px; color: white; min-width: 150px;">
                    <div style="font-size: 32px; font-weight: 700;">{total}</div>
                    <div style="font-size: 13px; opacity: 0.9;">Ofertas encontradas</div>
                </div>
                <div style="background: linear-gradient(135deg, #1a73e8, #1557b0); border-radius: 10px;
                            padding: 15px 25px; color: white; min-width: 150px;">
                    <div style="font-size: 32px; font-weight: 700;">{len(fuentes_conteo)}</div>
                    <div style="font-size: 13px; opacity: 0.9;">Fuentes consultadas</div>
                </div>
            </div>

            <div style="margin-top: 10px;">
                <p style="font-size: 13px; color: #666; margin: 5px 0;">
                    <strong>Fuentes:</strong> {resumen_fuentes if resumen_fuentes else "Ninguna fuente devolvio resultados"}
                </p>
            </div>

            <div style="margin-top: 12px;">
                <p style="font-size: 12px; color: #888; margin: 3px 0;"><strong>Palabras clave:</strong></p>
                <div>{palabras_badges}</div>
            </div>

            <div style="margin-top: 10px;">
                <p style="font-size: 12px; color: #888; margin: 3px 0;"><strong>Ubicaciones:</strong></p>
                <div>{ubicaciones_badges}</div>
            </div>
        </div>

        <!-- Tabla de resultados -->
        <div style="background-color: #ffffff; border-radius: 12px; overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background: linear-gradient(135deg, #1a1a2e, #16213e);">
                        <th style="padding: 14px 15px; text-align: left; color: #e94560;
                                   font-weight: 600; font-size: 13px; text-transform: uppercase;
                                   letter-spacing: 0.5px;">
                            Titulo / Fuente
                        </th>
                        <th style="padding: 14px 15px; text-align: left; color: #e94560;
                                   font-weight: 600; font-size: 13px; text-transform: uppercase;
                                   letter-spacing: 0.5px;">
                            Empresa
                        </th>
                        <th style="padding: 14px 15px; text-align: left; color: #e94560;
                                   font-weight: 600; font-size: 13px; text-transform: uppercase;
                                   letter-spacing: 0.5px;">
                            Ubicacion
                        </th>
                        <th style="padding: 14px 15px; text-align: left; color: #e94560;
                                   font-weight: 600; font-size: 13px; text-transform: uppercase;
                                   letter-spacing: 0.5px;">
                            Salario
                        </th>
                        <th style="padding: 14px 15px; text-align: left; color: #e94560;
                                   font-weight: 600; font-size: 13px; text-transform: uppercase;
                                   letter-spacing: 0.5px;">
                            Enlace
                        </th>
                        <th style="padding: 14px 15px; text-align: left; color: #e94560;
                                   font-weight: 600; font-size: 13px; text-transform: uppercase;
                                   letter-spacing: 0.5px;">
                            Fecha
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
            </table>
        </div>

        <!-- Pie de pagina -->
        <div style="text-align: center; padding: 20px; margin-top: 20px; color: #888; font-size: 12px;">
            <p>Generado automaticamente por Buscador de Trabajos v1.0</p>
            <p>Las ofertas pueden haber expirado. Verifica siempre en el sitio original.</p>
            <p style="margin-top: 10px;">
                <a href="https://remoteok.com" style="color: #1a73e8; margin: 0 5px;">RemoteOK</a> |
                <a href="https://www.indeed.com" style="color: #1a73e8; margin: 0 5px;">Indeed</a> |
                <a href="https://www.linkedin.com/jobs" style="color: #1a73e8; margin: 0 5px;">LinkedIn</a> |
                <a href="https://gamejobs.co" style="color: #1a73e8; margin: 0 5px;">GameJobs</a> |
                <a href="https://hitmarker.net" style="color: #1a73e8; margin: 0 5px;">Hitmarker</a> |
                <a href="https://remotive.com" style="color: #1a73e8; margin: 0 5px;">Remotive</a>
            </p>
        </div>
    </div>
</body>
</html>"""

    return html


# =====================================================================
# ENVIO DE CORREO ELECTRONICO
# =====================================================================

def enviar_correo(html_contenido: str, total_ofertas: int) -> bool:
    """
    Envia el reporte de trabajos por correo electronico usando Gmail SMTP.

    Requiere:
    - Verificacion en 2 pasos activada en la cuenta de Gmail
    - Contrasena de aplicacion generada (ver instrucciones al inicio del script)
    """
    if not GMAIL_APP_PASSWORD:
        logger.warning(
            "No se configuro la contrasena de aplicacion de Gmail. "
            "El correo NO sera enviado. Configura la variable GMAIL_APP_PASSWORD "
            "(ver instrucciones al inicio del script)."
        )
        return False

    try:
        logger.info(f"Preparando envio de correo a {GMAIL_DESTINATARIO}...")

        # Crear el mensaje de correo
        mensaje = MIMEMultipart("alternative")
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        mensaje["Subject"] = f"[Buscador Trabajos] {total_ofertas} ofertas encontradas - {fecha_hoy}"
        mensaje["From"] = GMAIL_REMITENTE
        mensaje["To"] = GMAIL_DESTINATARIO

        # Version texto plano (por si el cliente no soporta HTML)
        texto_plano = (
            f"Buscador de Trabajos - Reporte del {fecha_hoy}\n\n"
            f"Se encontraron {total_ofertas} ofertas de trabajo.\n\n"
            f"Abre el archivo HTML adjunto o visualiza este correo en un "
            f"cliente que soporte HTML para ver la tabla completa.\n"
        )
        parte_texto = MIMEText(texto_plano, "plain", "utf-8")
        parte_html = MIMEText(html_contenido, "html", "utf-8")

        # Agregar ambas versiones (el cliente de correo elegira la mejor)
        mensaje.attach(parte_texto)
        mensaje.attach(parte_html)

        # Conectar al servidor SMTP de Gmail
        logger.info("Conectando al servidor SMTP de Gmail...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(GMAIL_REMITENTE, GMAIL_APP_PASSWORD)
            servidor.sendmail(GMAIL_REMITENTE, GMAIL_DESTINATARIO, mensaje.as_string())

        logger.info(f"Correo enviado exitosamente a {GMAIL_DESTINATARIO}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Error de autenticacion con Gmail. Verifica que:\n"
            "  1. La contrasena de aplicacion sea correcta\n"
            "  2. La verificacion en 2 pasos este activada\n"
            "  3. El correo remitente sea correcto"
        )
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP al enviar correo: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar correo: {e}")
        return False


# =====================================================================
# CACHE - Para no buscar repetidamente los mismos resultados
# =====================================================================

def cargar_cache() -> Dict:
    """Carga el cache de resultados anteriores."""
    try:
        if os.path.exists(ARCHIVO_CACHE):
            with open(ARCHIVO_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"ultima_busqueda": "", "ids_vistos": []}


def guardar_cache(ofertas: List[OfertaTrabajo]):
    """Guarda los IDs de ofertas encontradas para identificar nuevas en el futuro."""
    try:
        cache = {
            "ultima_busqueda": datetime.now().isoformat(),
            "ids_vistos": [o.identificador_unico() for o in ofertas],
        }
        with open(ARCHIVO_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar el cache: {e}")


# =====================================================================
# FUNCION PRINCIPAL
# =====================================================================

def main():
    """
    Funcion principal que coordina toda la busqueda:
    1. Busca en todas las fuentes
    2. Elimina duplicados
    3. Genera el reporte HTML
    4. Guarda el archivo HTML
    5. Envia el correo electronico
    """
    logger.info("=" * 70)
    logger.info("INICIANDO BUSQUEDA DE TRABAJOS - UNREAL ENGINE / GAME DEV")
    logger.info("=" * 70)
    logger.info(f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Palabras clave: {', '.join(PALABRAS_CLAVE)}")
    logger.info(f"Ubicaciones: {', '.join(UBICACIONES[:5])}...")
    logger.info("-" * 70)

    # Crear sesion HTTP reutilizable
    sesion = crear_sesion_http()
    todas_las_ofertas: List[OfertaTrabajo] = []

    # ---------------------------------------------------------------
    # PASO 1: Buscar en todas las fuentes
    # ---------------------------------------------------------------
    fuentes_busqueda = [
        ("RemoteOK", buscar_remoteok),
        ("Indeed RSS", buscar_indeed_rss),
        ("LinkedIn", buscar_linkedin_publico),
        ("GameJobs.co", buscar_gamedevjobs),
        ("Hitmarker", buscar_hitmarker),
        ("Working Nomads", buscar_workingnomads),
        ("Remotive", buscar_remotive),
        ("Jooble RSS", buscar_jooble_rss),
    ]

    for nombre, funcion_busqueda in fuentes_busqueda:
        try:
            logger.info(f"\n--- Consultando: {nombre} ---")
            resultados = funcion_busqueda(sesion)
            todas_las_ofertas.extend(resultados)
        except Exception as e:
            logger.error(f"Error critico al buscar en {nombre}: {e}")
            continue

    logger.info("-" * 70)
    logger.info(f"Total de ofertas encontradas (antes de eliminar duplicados): {len(todas_las_ofertas)}")

    # ---------------------------------------------------------------
    # PASO 2: Eliminar duplicados
    # ---------------------------------------------------------------
    ofertas_unicas = eliminar_duplicados(todas_las_ofertas)
    logger.info(f"Total de ofertas unicas: {len(ofertas_unicas)}")

    # Ordenar por fecha (las mas recientes primero)
    # Las ofertas con fecha valida aparecen primero
    ofertas_unicas.sort(key=lambda o: o.fecha_publicacion if o.fecha_publicacion != "Sin fecha" else "ZZZ")

    # ---------------------------------------------------------------
    # PASO 3: Generar reporte HTML
    # ---------------------------------------------------------------
    fecha_busqueda = datetime.now().strftime("%d/%m/%Y a las %H:%M")
    html_reporte = generar_html(ofertas_unicas, fecha_busqueda)

    # ---------------------------------------------------------------
    # PASO 4: Guardar archivo HTML
    # ---------------------------------------------------------------
    try:
        with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
            f.write(html_reporte)
        logger.info(f"Reporte HTML guardado en: {ARCHIVO_HTML}")
    except IOError as e:
        logger.error(f"Error al guardar archivo HTML: {e}")

    # ---------------------------------------------------------------
    # PASO 5: Enviar correo electronico
    # ---------------------------------------------------------------
    correo_enviado = enviar_correo(html_reporte, len(ofertas_unicas))

    # ---------------------------------------------------------------
    # PASO 6: Guardar cache
    # ---------------------------------------------------------------
    guardar_cache(ofertas_unicas)

    # ---------------------------------------------------------------
    # RESUMEN FINAL
    # ---------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN DE LA BUSQUEDA")
    logger.info("=" * 70)
    logger.info(f"  Ofertas encontradas:     {len(ofertas_unicas)}")
    logger.info(f"  Duplicados eliminados:   {len(todas_las_ofertas) - len(ofertas_unicas)}")
    logger.info(f"  Archivo HTML:            {ARCHIVO_HTML}")
    logger.info(f"  Correo enviado:          {'Si' if correo_enviado else 'No (revisa la configuracion)'}")
    logger.info(f"  Archivo de log:          {ARCHIVO_LOG}")
    logger.info("=" * 70)

    # Mostrar las primeras ofertas en consola como preview
    if ofertas_unicas:
        logger.info("\n--- PREVIEW: Primeras 10 ofertas ---\n")
        for i, oferta in enumerate(ofertas_unicas[:10], 1):
            logger.info(f"  {i}. {oferta.titulo}")
            logger.info(f"     Empresa: {oferta.empresa or 'N/A'} | Ubicacion: {oferta.ubicacion}")
            logger.info(f"     Salario: {oferta.salario} | Fuente: {oferta.fuente}")
            logger.info(f"     Enlace: {oferta.enlace}")
            logger.info("")

    # Abrir el archivo HTML en el navegador automaticamente (solo en Windows)
    try:
        if sys.platform == "win32" and os.path.exists(ARCHIVO_HTML):
            os.startfile(ARCHIVO_HTML)
            logger.info("Se abrio el reporte HTML en el navegador.")
    except Exception:
        pass  # No es critico si no se puede abrir

    return ofertas_unicas


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================
if __name__ == "__main__":
    try:
        resultados = main()
        print(f"\nBusqueda completada. Se encontraron {len(resultados)} ofertas.")
        print(f"Revisa el archivo: {ARCHIVO_HTML}")
    except KeyboardInterrupt:
        print("\nBusqueda cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
