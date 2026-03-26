"""Busca ofertas ACTIVAS en Greenhouse usando la API pública"""
import requests
import json

# Empresas de gaming/UE que usan Greenhouse
companies = [
    "epicgames", "bungie", "bulletfarm", "cloudchamberen", "bitreactor",
    "arenanet", "tripwireinteractive", "digitalextremes", "firaxis",
    "pubgemea", "pubgmadison", "pubgsanramon", "nimblegiant",
    "hoyoverse", "kraftonamericas", "studiokraftonboard",
    "sonyinteractiveentertainmentglobal", "neonkoi",
    "onistudios", "asubsidiaryofsca", "mrbeastyoutube",
    "frgjobs", "worldsuntold", "criticalmass", "catdaddy",
    "mediamonks", "insomniac", "wevr", "unknownworlds",
    "ingenuitystudios", "appliedintuition", "crystaldynamics",
    "2k", "mobentertainment", "hardsuitlabs",
    "nightdivestudios", "turtlerockstudios", "gravitywell",
    "higharc",
]

ue_keywords = [
    "unreal", "ue5", "ue4", "blueprint", "environment artist",
    "technical artist", "vfx artist", "character artist", "level design",
    "lighting artist", "prop artist", "gameplay programmer",
    "game programmer", "engine programmer", "3d artist", "animator",
    "materials artist", "hard surface", "rigging", "cinematic",
    "game developer", "game engineer", "ui artist",
]

all_jobs = []

for company in companies:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            continue
        data = resp.json()
        jobs = data.get("jobs", [])
        if not jobs:
            continue

        for job in jobs:
            title = job.get("title", "")
            job_url = job.get("absolute_url", "")
            location = job.get("location", {}).get("name", "")
            job_id = job.get("id", "")
            updated = job.get("updated_at", "")

            # Filtrar por keywords UE
            title_lower = title.lower()
            is_ue = any(kw in title_lower for kw in ue_keywords)

            if is_ue:
                all_jobs.append({
                    "empresa": company,
                    "titulo": title,
                    "url": job_url,
                    "ubicacion": location,
                    "actualizado": updated,
                    "id": job_id,
                })
                print(f"  [{company}] {title} - {location} ({updated[:10]})")

        if any(j["empresa"] == company for j in all_jobs):
            count = sum(1 for j in all_jobs if j["empresa"] == company)
            print(f"  -> {company}: {count} ofertas UE de {len(jobs)} total")
    except Exception as e:
        print(f"  ERROR {company}: {e}")

print(f"\n{'='*60}")
print(f"TOTAL ofertas UE activas: {len(all_jobs)}")
print(f"{'='*60}")

# Ordenar por fecha de actualización (más reciente primero)
all_jobs.sort(key=lambda x: x["actualizado"], reverse=True)

print("\nTop 30 más recientes:")
for i, job in enumerate(all_jobs[:30], 1):
    print(f"{i}. [{job['actualizado'][:10]}] {job['titulo']} @ {job['empresa']}")
    print(f"   URL: {job['url']}")
    print(f"   Location: {job['ubicacion']}")

# Guardar como Python dict para copiar al script
print(f"\n\n# To copy into src/auto_applicant.py:")
for job in all_jobs:
    print(f'    {{"titulo": "{job["titulo"]}", "empresa": "{job["empresa"]}", "ubicacion": "{job["ubicacion"]}", "salario": "", "url": "{job["url"]}", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"}},')
