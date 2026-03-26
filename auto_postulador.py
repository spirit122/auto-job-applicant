#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
AUTO-POSTULADOR DE TRABAJOS - Unreal Engine Developer
=============================================================
Este script busca ofertas de trabajo, genera cartas de
presentación adaptadas y postula automáticamente.

Autor: spirit122
=============================================================

CONFIGURACIÓN DE EMAIL (para recibir notificaciones):
1. Ve a https://myaccount.google.com/security
2. Activa la verificación en 2 pasos
3. Ve a https://myaccount.google.com/apppasswords
4. Selecciona "Correo" y "Otro (AutoPostulador)"
5. Copia la contraseña de 16 caracteres
6. Pégala en GMAIL_APP_PASSWORD más abajo
"""

import requests
import json
import os
import time
import logging
import re
import hashlib
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
# CONFIGURACIÓN PERSONAL - EDITA TUS DATOS AQUÍ
# ============================================================
DATOS_PERSONALES = {
    "nombre": os.environ.get("APPLICANT_FIRST_NAME", "Your Name"),
    "apellido": os.environ.get("APPLICANT_LAST_NAME", "Your Last Name"),
    "nombre_completo": os.environ.get("APPLICANT_FULL_NAME", "Your Full Name"),
    "email": os.environ.get("APPLICANT_EMAIL", "your@email.com"),
    "telefono": os.environ.get("APPLICANT_PHONE", "+1234567890"),
    "ciudad": os.environ.get("APPLICANT_CITY", "Your City"),
    "pais": os.environ.get("APPLICANT_COUNTRY", "Your Country"),
    "linkedin": os.environ.get("APPLICANT_LINKEDIN", ""),
    "portfolio": os.environ.get("APPLICANT_PORTFOLIO", ""),
    "graduation_year": os.environ.get("APPLICANT_GRAD_YEAR", "2020"),
    "gaming_experience": os.environ.get("APPLICANT_GAMING_EXP", ""),
    "titulo": os.environ.get("APPLICANT_TITLE", "Developer"),
    "experiencia_anos": os.environ.get("APPLICANT_EXP_YEARS", "5"),
    "cv_path": os.environ.get("APPLICANT_CV_PATH", "cv.pdf"),
    "cv_path_en": os.environ.get("APPLICANT_CV_PATH_EN", "cv_en.pdf"),
}

# ============================================================
# OFERTAS CONOCIDAS - URLs de ofertas reales encontradas
# Agrega aquí URLs de ofertas que encuentres manualmente
# El bot intentará postular a cada una automáticamente
# ============================================================
OFERTAS_CONOCIDAS = [
    # ============================================================
    # GREENHOUSE API - URLs VERIFICADAS ACTIVAS (13 Feb 2026)
    # Solo empresas reconocidas de gaming/tech
    # ============================================================
    # --- Cloud Chamber (BioShock) - 6 ofertas activas ---
    {"titulo": "Lead VFX Artist", "empresa": "Cloud Chamber (BioShock)", "ubicacion": "Novato, California", "salario": "", "url": "https://job-boards.greenhouse.io/cloudchamberen/jobs/7494766003", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead VFX Artist", "empresa": "Cloud Chamber (BioShock)", "ubicacion": "Montreal, Canada", "salario": "", "url": "https://job-boards.greenhouse.io/cloudchamberen/jobs/7494768003", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Principal Character Technical Animator", "empresa": "Cloud Chamber (BioShock)", "ubicacion": "Novato, California", "salario": "", "url": "https://job-boards.greenhouse.io/cloudchamberen/jobs/7535701003", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Principal Character Technical Animator", "empresa": "Cloud Chamber (BioShock)", "ubicacion": "Montreal, Canada", "salario": "", "url": "https://job-boards.greenhouse.io/cloudchamberen/jobs/7535699003", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Character Artist", "empresa": "Cloud Chamber (BioShock)", "ubicacion": "Montreal, Canada", "salario": "", "url": "https://job-boards.greenhouse.io/cloudchamberen/jobs/7592436003", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Character Artist", "empresa": "Cloud Chamber (BioShock)", "ubicacion": "Novato, California", "salario": "", "url": "https://job-boards.greenhouse.io/cloudchamberen/jobs/7592438003", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Insomniac Games (Spider-Man, Ratchet & Clank) - 2 ofertas ---
    {"titulo": "VFX Artist (CONTRACT)", "empresa": "Insomniac Games", "ubicacion": "Remote, US", "salario": "", "url": "https://job-boards.greenhouse.io/insomniac/jobs/5684436004", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Animator (CONTRACT)", "empresa": "Insomniac Games", "ubicacion": "Burbank, CA", "salario": "", "url": "https://job-boards.greenhouse.io/insomniac/jobs/5783228004", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Bungie (Marathon, Destiny) - 1 oferta ---
    {"titulo": "Marathon Senior Lighting Artist", "empresa": "Bungie", "ubicacion": "Remote, US", "salario": "", "url": "https://job-boards.greenhouse.io/bungie/jobs/5729343004", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Sony / PlayStation - 2 ofertas ---
    {"titulo": "Hard Surface Modeler", "empresa": "Sony Interactive Entertainment", "ubicacion": "Montreal, Canada", "salario": "", "url": "https://job-boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/5796350004", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Sr Character Technical Artist (Contract)", "empresa": "Sony Interactive Entertainment", "ubicacion": "Los Angeles, CA", "salario": "", "url": "https://job-boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/5711837004", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Digital Extremes (Warframe) - 1 oferta ---
    {"titulo": "Animator", "empresa": "Digital Extremes", "ubicacion": "London, Ontario or Remote", "salario": "", "url": "https://job-boards.greenhouse.io/digitalextremes/jobs/5047152007", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Crystal Dynamics (Tomb Raider) - 1 oferta ---
    {"titulo": "Level Design Intern", "empresa": "Crystal Dynamics", "ubicacion": "Hybrid/Remote, US", "salario": "", "url": "https://job-boards.greenhouse.io/crystaldynamics/jobs/4640170005", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Nightdive Studios (System Shock) - 2 ofertas ---
    {"titulo": "Lead Animator (Contract)", "empresa": "Nightdive Studios", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/nightdivestudios/jobs/5101963008", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Character Artist (Contract)", "empresa": "Nightdive Studios", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/nightdivestudios/jobs/5099598008", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Gravity Well - 1 oferta ---
    {"titulo": "VFX Artist", "empresa": "Gravity Well", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/gravitywell/jobs/5007025007", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- KRAFTON (PUBG) - 2 ofertas ---
    {"titulo": "Principal 3C Gameplay Programmer", "empresa": "KRAFTON Montreal", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/studiokraftonboard/jobs/8362528002", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Character Artist", "empresa": "KRAFTON Montreal", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/studiokraftonboard/jobs/8286316002", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- HoYoverse (Genshin Impact) - 1 oferta ---
    {"titulo": "Gameplay Animator", "empresa": "HoYoverse", "ubicacion": "Singapore", "salario": "", "url": "https://job-boards.greenhouse.io/hoyoverse/jobs/4988359007", "descripcion": "Active Greenhouse job", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Guerrilla Games (Horizon) - 2 ofertas ---
    {"titulo": "Cinematic Technical Animator", "empresa": "Guerrilla Games", "ubicacion": "Amsterdam, Netherlands", "salario": "", "url": "https://job-boards.greenhouse.io/guerrilla-games/jobs/5778235004", "descripcion": "Cinematic Technical Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Creature Animator", "empresa": "Guerrilla Games", "ubicacion": "Amsterdam, Netherlands", "salario": "", "url": "https://job-boards.greenhouse.io/guerrilla-games/jobs/5524927004", "descripcion": "Lead Creature Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Scopely - 1 oferta ---
    {"titulo": "Senior Render Artist", "empresa": "Scopely", "ubicacion": "Barcelona/UK/Dublin", "salario": "", "url": "https://job-boards.greenhouse.io/scopely/jobs/5108862008", "descripcion": "Senior Render Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Singularity 6 (Palia) - 2 ofertas ---
    {"titulo": "Technical Artist (Environment Tool)", "empresa": "Singularity 6", "ubicacion": "Remote, Canada", "salario": "", "url": "https://job-boards.greenhouse.io/singularity6/jobs/5719828004", "descripcion": "Technical Artist Environment UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Artist (Environment)", "empresa": "Singularity 6", "ubicacion": "Remote, Canada", "salario": "", "url": "https://job-boards.greenhouse.io/singularity6/jobs/5719843004", "descripcion": "Senior Technical Artist Environment UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Firesprite (Sony UK) - 1 oferta ---
    {"titulo": "Lead Lighting Artist", "empresa": "Firesprite (Sony)", "ubicacion": "Remote, UK", "salario": "", "url": "https://job-boards.greenhouse.io/firesprite/jobs/5619722004", "descripcion": "Lead Lighting Artist UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Naughty Dog (The Last of Us, Uncharted) - 5 ofertas ---
    {"titulo": "Environment Concept Artist", "empresa": "Naughty Dog", "ubicacion": "Santa Monica, CA", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5778489004", "descripcion": "Environment Concept Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Gameplay Programmer", "empresa": "Naughty Dog", "ubicacion": "Santa Monica, CA", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5790564004", "descripcion": "Gameplay Programmer", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lighting Artist, Cinematic (Contingent)", "empresa": "Naughty Dog", "ubicacion": "Santa Monica, CA", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5762470004", "descripcion": "Cinematic Lighting Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lighting Artist, Environment (Contingent)", "empresa": "Naughty Dog", "ubicacion": "Santa Monica, CA", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5762460004", "descripcion": "Environment Lighting Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Artist (Character)", "empresa": "Naughty Dog", "ubicacion": "Santa Monica, CA", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5706469004", "descripcion": "Senior Technical Artist Character", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Hangar 13 (Mafia series) - 11 ofertas ---
    {"titulo": "Lead Lighting Artist", "empresa": "Hangar 13", "ubicacion": "Brighton, UK", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7596481003", "descripcion": "Lead Lighting Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Animator", "empresa": "Hangar 13", "ubicacion": "Prague, Czech Republic", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7533084003", "descripcion": "Lead Technical Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Animator", "empresa": "Hangar 13", "ubicacion": "Brno, Czech Republic", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7533080003", "descripcion": "Lead Technical Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Animator", "empresa": "Hangar 13", "ubicacion": "Brighton, UK", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7530868003", "descripcion": "Lead Technical Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Artist - Shaders", "empresa": "Hangar 13", "ubicacion": "Brno, Czech Republic", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7527472003", "descripcion": "Lead Tech Artist Shaders", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Artist - Shaders", "empresa": "Hangar 13", "ubicacion": "Brighton, UK", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7533147003", "descripcion": "Lead Tech Artist Shaders", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Artist - Tools and Pipeline", "empresa": "Hangar 13", "ubicacion": "Brighton, UK", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7533137003", "descripcion": "Lead Tech Artist Tools Pipeline", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Artist - Tools and Pipeline", "empresa": "Hangar 13", "ubicacion": "Brno, Czech Republic", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7527476003", "descripcion": "Lead Tech Artist Tools Pipeline", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead VFX Artist", "empresa": "Hangar 13", "ubicacion": "Brighton, UK", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7526256003", "descripcion": "Lead VFX Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Animator", "empresa": "Hangar 13", "ubicacion": "Brno, Czech Republic", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7533089003", "descripcion": "Senior Gameplay Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Animator", "empresa": "Hangar 13", "ubicacion": "Brighton, UK", "salario": "", "url": "https://job-boards.greenhouse.io/hangar13/jobs/7526247003", "descripcion": "Senior Gameplay Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Riot Games (LoL, VALORANT) - 1 oferta ---
    {"titulo": "Concept Art Lead - VALORANT Premium Content", "empresa": "Riot Games", "ubicacion": "Los Angeles, USA", "salario": "", "url": "https://job-boards.greenhouse.io/riotgames/jobs/7336875", "descripcion": "Concept Art Lead VALORANT", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # ============================================================
    # LEVER - Empresas reconocidas
    # ============================================================
    # --- Skydance Interactive - 2 ofertas ---
    {"titulo": "Lead Technical Artist", "empresa": "Skydance Interactive", "ubicacion": "Santa Monica/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/0c2b0ae2-d53a-44f9-8a93-9371d8a6a61f", "descripcion": "Lead Technical Artist UE", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "AI Game Tech, Technical Director", "empresa": "Skydance Interactive", "ubicacion": "Santa Monica, CA", "salario": "", "url": "https://jobs.lever.co/skydance/8cd63554-2eab-4933-9dc6-9c0f88ea0dc2", "descripcion": "AI Game Tech Director UE", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Xsolla / Black Ember ---
    {"titulo": "Lead UE Programmer (6mo Contract)", "empresa": "Xsolla (Black Ember)", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/xsolla/88600493-567f-41dd-8a56-d77175deb5bd", "descripcion": "Lead UE5 programmer FPS", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Unreal Engine Developer", "empresa": "Xsolla (Black Ember)", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/xsolla/6b80a858-1882-4c1a-8a75-de4332b261e2", "descripcion": "Senior UE developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Programmer, AI & Behavior (UE5)", "empresa": "Xsolla (Black Ember)", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/xsolla/3fe76a7d-618f-452e-b79a-ff03021505c0", "descripcion": "AI behavior programmer UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Gameplay Programmer (UE5)", "empresa": "Xsolla (Black Ember)", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/xsolla/e78a1a55-891a-4a52-ad5b-8845d77f74e7", "descripcion": "Gameplay programmer UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Level Designer (UE5)", "empresa": "Xsolla (Black Ember)", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/xsolla/19f690a9-693a-4a1a-8d44-057138643dc6", "descripcion": "Level designer UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Blackbird Interactive (Homeworld) ---
    {"titulo": "Intermediate Platforms Engineer (UE5)", "empresa": "Blackbird Interactive", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/04db30a0-5a52-4efe-b12d-c1b36b118b4e", "descripcion": "Platforms engineer UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Associate Gameplay Engineer (UE5)", "empresa": "Blackbird Interactive", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/fd138c52-672a-4070-896e-d3751394fa32", "descripcion": "Associate gameplay engineer UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Sr/Int Software Engineer (UE5 Online)", "empresa": "Blackbird Interactive", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/6f33d670-082d-4f87-a02a-18e08efaea13", "descripcion": "Software engineer UE5 crossplay", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Blackbird Interactive (NEW art roles) ---
    {"titulo": "3D Artist (5-month Contract)", "empresa": "Blackbird Interactive", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/0c8c4eb1-4aa5-4e7d-bef7-222546c9bea1", "descripcion": "3D Artist Contract", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "3D Generalist (UE)", "empresa": "Blackbird Interactive", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/383e065f-6db2-448b-b311-090f2b6b6666", "descripcion": "3D Generalist Unreal Engine", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Concept Artist (5-month Contract)", "empresa": "Blackbird Interactive", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/6ef24502-2b3b-41c7-817b-13b10322011e", "descripcion": "Concept Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Environment and Prop Artist (8-month Contract)", "empresa": "Blackbird Interactive", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/e93eed62-d44b-4664-9771-2fb4cf2c29c5", "descripcion": "Environment Prop Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Lead 3D Artist", "empresa": "Blackbird Interactive", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/7bc782d4-be7e-43e3-84e9-4f0c0862874e", "descripcion": "Lead 3D Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Theorycraft Games (SUPERVIVE) ---
    {"titulo": "Future Opportunities (SUPERVIVE)", "empresa": "Theorycraft Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/theorycraftgames/598cb8e2-791a-4e53-a6e1-9066bff2428d", "descripcion": "Open application SUPERVIVE UE", "fuente": "Lever", "fecha": "Febrero 2026"},
    # ============================================================
    # SMARTRECRUITERS - Empresas reconocidas
    # ============================================================
    # --- CD PROJEKT RED (The Witcher, Cyberpunk 2077) ---
    {"titulo": "Senior Engine Programmer - UE", "empresa": "CD PROJEKT RED", "ubicacion": "Warsaw/Remote", "salario": "", "url": "https://jobs.smartrecruiters.com/CDPROJEKTRED/743999858930281-senior-engine-programmer-unreal-engine", "descripcion": "Senior engine programmer UE Witcher", "fuente": "SmartRecruiters", "fecha": "Febrero 2026"},
    {"titulo": "Game Programmer - UE", "empresa": "CD PROJEKT RED", "ubicacion": "Warsaw/Remote", "salario": "", "url": "https://jobs.smartrecruiters.com/CDPROJEKTRED/743999852847951-game-programmer-unreal-engine", "descripcion": "Game programmer UE Witcher", "fuente": "SmartRecruiters", "fecha": "Febrero 2026"},
    {"titulo": "Core Tech Engineer - UE", "empresa": "CD PROJEKT RED", "ubicacion": "Warsaw/Remote", "salario": "", "url": "https://jobs.smartrecruiters.com/CDPROJEKTRED/743999843894327-core-tech-engineer-unreal-engine", "descripcion": "Core tech engineer UE Witcher", "fuente": "SmartRecruiters", "fecha": "Febrero 2026"},
    # ============================================================
    # WORKABLE - Empresas con ofertas UE verificadas (Feb 2026)
    # ============================================================
    # --- Jackbox Games ---
    {"titulo": "Senior Unreal Engine Developer", "empresa": "Jackbox Games", "ubicacion": "Chicago, IL (Remote-friendly)", "salario": "$148,985-$228,055", "url": "https://apply.workable.com/jackbox-games/j/359FBCCBA7/", "descripcion": "UE C++ multiplayer, EOS, matchmaking", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Technical Director / Senior Principal Engineer - UE", "empresa": "Jackbox Games", "ubicacion": "Chicago, IL (Remote-friendly)", "salario": "$172,845-$222,845", "url": "https://apply.workable.com/jackbox-games/j/9CDD3A2F61/", "descripcion": "Lead core systems architecture UE multiplayer", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Pixomondo (Sony) ---
    {"titulo": "Unreal Engine Software Developer", "empresa": "Pixomondo (Sony)", "ubicacion": "Toronto/Vancouver/London (Hybrid)", "salario": "", "url": "https://apply.workable.com/pxo/j/B8BE9B326C/", "descripcion": "UE C++ Virtual Production pipeline", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Engine Operator", "empresa": "Pixomondo (Sony)", "ubicacion": "Toronto, ON", "salario": "", "url": "https://apply.workable.com/pxo/j/A7F858B10F/", "descripcion": "On-set UE operator Virtual Production", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Sperasoft ---
    {"titulo": "Senior C++ Developer with Unreal Engine", "empresa": "Sperasoft", "ubicacion": "Poland (Krakow) / Remote", "salario": "", "url": "https://apply.workable.com/sperasoft/j/49FE4F5F1E/", "descripcion": "AAA game co-development C++ UE", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- BeamNG ---
    {"titulo": "VFX / Unreal Engine Programmer", "empresa": "BeamNG GmbH", "ubicacion": "Bremen, Germany (Remote)", "salario": "", "url": "https://apply.workable.com/beamng/j/E666DFD605/", "descripcion": "VFX for vehicle simulation UE", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Velan Studios ---
    {"titulo": "Visual Effects (VFX) Artist", "empresa": "Velan Studios", "ubicacion": "Troy, NY (Remote)", "salario": "", "url": "https://apply.workable.com/velanstudios/j/6D05895C8C/", "descripcion": "VFX Artist UE Niagara", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Visual Effects (VFX) Artist - Contract", "empresa": "Velan Studios", "ubicacion": "Troy, NY (Remote)", "salario": "", "url": "https://apply.workable.com/velanstudios/j/01683A6272/", "descripcion": "Contract VFX Artist UE", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Escape Velocity Entertainment (AAA, fully remote) ---
    {"titulo": "Technical Artist", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/4CC5CAD993/", "descripcion": "UE Geometry Script, PCG, Houdini", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Artist", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/64E59833FF/", "descripcion": "UE shaders, PBR, materials optimization", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Associate Technical Artist", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/2FE06D118D/", "descripcion": "Junior tech art UE mobile optimization", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "UI Artist", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/A1B315CF38/", "descripcion": "UI Art in UE5", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior UI Artist", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/57BAC70DBD/", "descripcion": "Senior UI Art in UE5", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Lead UI Artist - Platform", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/923A7DA146/", "descripcion": "Lead UI Art in UE5", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "UI Engineer", "empresa": "Escape Velocity Entertainment", "ubicacion": "NA/Canada/Europe (Remote)", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/3978187AFE/", "descripcion": "UI engineering UE", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- NinjaTech AI ---
    {"titulo": "Technical Artist - UE5 (MetaHumans)", "empresa": "NinjaTech AI", "ubicacion": "Palo Alto, CA", "salario": "", "url": "https://apply.workable.com/ninjatech-ai/j/02CAB2024E/", "descripcion": "UE5 MetaHumans AI digital humans", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "3D Design Engineer - UE5", "empresa": "NinjaTech AI", "ubicacion": "Palo Alto, CA", "salario": "", "url": "https://apply.workable.com/ninjatech-ai/j/EF1953A5A7/", "descripcion": "3D design UE5 generative AI", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Magic Media (Remote) ---
    {"titulo": "Senior 3D Environment Artist (Unreal)", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/8EF46A21E5/", "descripcion": "AAA environment art UE5 PBR", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Engine Networking Developer", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/11C8EA0321/", "descripcion": "UE networking gameplay multiplayer", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Programmer", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/68FA0B1226/", "descripcion": "Core UE game programming", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Lead Unreal & C++ Engineer", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/1B37104E91/", "descripcion": "Lead UE C++ engineering", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Saltwater Games ---
    {"titulo": "Technical Artist (Unreal Engine)", "empresa": "Saltwater Games", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/saltwatergames/j/2DB70D3B64/", "descripcion": "UE shaders Lumen Nanite World Partition", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Studio Gobo (Keywords) ---
    {"titulo": "Lead VFX Artist", "empresa": "Studio Gobo", "ubicacion": "Brighton, UK", "salario": "", "url": "https://apply.workable.com/studiogobo/j/83AA28277A/", "descripcion": "Lead VFX AAA console game UE", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- High Voltage Software ---
    {"titulo": "Technical Artist", "empresa": "High Voltage Software", "ubicacion": "Hoffman Estates, IL / New Orleans, LA", "salario": "", "url": "https://apply.workable.com/high-voltage-software/j/8EA1C0CA7C/", "descripcion": "Game tech art UE Niagara Blueprints", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- BRON Studios ---
    {"titulo": "Character Surfacing Artist", "empresa": "BRON Studios", "ubicacion": "Remote / Vancouver", "salario": "", "url": "https://apply.workable.com/bron-studios/j/2D95F6CF7C/", "descripcion": "Texturing shader dev UE animation", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "UE4 Lighting/Compositing Artist", "empresa": "BRON Studios", "ubicacion": "Remote / Los Angeles", "salario": "", "url": "https://apply.workable.com/bron-studios/j/F788E8EAB5/", "descripcion": "Lighting compositing UE animation", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- PTW (Chile/Spain/Argentina/Mexico!) ---
    {"titulo": "Lead VFX Artist | Unity and Unreal", "empresa": "PTW", "ubicacion": "Spain/Chile/Argentina/Mexico (Remote)", "salario": "", "url": "https://apply.workable.com/ptw-i/j/FE47787DCE/", "descripcion": "Lead VFX AAA UE CASCADE particles shaders", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- coherence ---
    {"titulo": "Senior Unreal Engineer", "empresa": "coherence", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/coherence/j/D911DF30F6/", "descripcion": "UE SDK multiplayer platform C++", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Spree3D ---
    {"titulo": "Unreal Engine Developer (Tools)", "empresa": "Spree3D", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/spree3d/j/5F9C43F412/", "descripcion": "C++ tooling virtual production UE", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- mod.io ---
    {"titulo": "Multimedia Specialist - UE Library Developer", "empresa": "mod.io", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/modio/j/51C2E6108F/", "descripcion": "UE library dev UGC platform", "fuente": "Workable", "fecha": "Febrero 2026"},
    # ============================================================
    # ASHBY - Ofertas UE verificadas (Feb 2026)
    # ============================================================
    # --- Worlds (Epic Games veterans, remote, UE5 PC titles) - 8 ofertas ---
    {"titulo": "Technical Director - Unreal Engine", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/580f4f1f-e239-4a93-88db-1b17959de49a", "descripcion": "Lead 10+ UE devs unannounced PC title", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Lead Unreal VFX Artist (Niagara)", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/31b8b106-93cc-4991-94d9-0aa58787479f", "descripcion": "VFX Niagara UE5 PC game", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Unreal VFX - Niagara", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/e7d1e65c-6c97-47af-9b45-ef126b616805", "descripcion": "Niagara VFX abilities environment UE5", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Tech Artist - Unreal", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/8c72b6f7-ff8c-4663-9264-38e6eecedfc8", "descripcion": "Tech artist UE pipeline Epic veterans", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Cinematics Artist - Unreal", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/32d58954-b309-4fa7-bccf-15b174c1932f", "descripcion": "Cinematics sequencer UE PC game", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "3D Generalist", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/71436a62-cbe6-4a67-a698-0f0276bbb9b5", "descripcion": "3D assets for UE5 3+ years exp", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Game Capture Artist", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/ca53a084-f794-45bd-8d6f-a8fda30547ff", "descripcion": "Game capture trailers UE5 PC title", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Gameplay Programmer (Blueprints)", "empresa": "Worlds", "ubicacion": "Remote (Worldwide)", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/2ad77d83-76c7-4e04-bd4d-b4d4a3e9c2fb", "descripcion": "Gameplay Blueprints UE5 Epic veterans", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Voodoo (#3 mobile publisher) ---
    {"titulo": "3D Unreal Generalist", "empresa": "Voodoo", "ubicacion": "Paris, France", "salario": "", "url": "https://jobs.ashbyhq.com/voodoo/d01dc567-8d0b-4733-8b93-b5bf8d2b7cdb", "descripcion": "3D UE Generalist creative marketing", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Pixaera (UE5 Safety Training) ---
    {"titulo": "Senior Animator", "empresa": "Pixaera", "ubicacion": "Europe - Remote", "salario": "", "url": "https://jobs.ashbyhq.com/pixaera/0a4e0419-93f3-42d3-bcba-e381d695947d", "descripcion": "Character animation UE 5.6 Mocap Sequencer MetaHuman", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Bifrost AI (NASA, defense) ---
    {"titulo": "Unreal Engine Generalist", "empresa": "Bifrost AI", "ubicacion": "Singapore", "salario": "", "url": "https://jobs.ashbyhq.com/Bifrost/cba11f65-6197-4447-9ae6-5474c21de25c", "descripcion": "Photorealistic 3D environments UE", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Methodical Games (ex-Epic Fortnite/Paragon/Gears) ---
    {"titulo": "Principal Character Artist", "empresa": "Methodical Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/Methodical-Careers/dbad745d-0094-4b9c-a080-b32989dec899", "descripcion": "Principal char artist Epic veterans UE", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Principal Technical Artist", "empresa": "Methodical Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/Methodical-Careers/c49c9a1f-074e-4f7f-acfa-aaa5416d843e", "descripcion": "Principal tech artist Epic veterans UE", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # ============================================================
    # NUEVAS OFERTAS - Febrero 2026 (busqueda 13 Feb sesion 2)
    # ============================================================
    # --- Nimble Giant / Saber Interactive (CHILE!) ---
    {"titulo": "Senior Game Programmer", "empresa": "Nimble Giant (Saber Interactive)", "ubicacion": "Chile/Argentina/Peru/Uruguay", "salario": "", "url": "https://boards.greenhouse.io/nimblegiant/jobs/169498", "descripcion": "C++ UE AAA live ops - LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Larian Studios (Baldur's Gate 3) ---
    {"titulo": "Junior Cinematic Animator", "empresa": "Larian Studios", "ubicacion": "Guildford, UK / Dublin / KL", "salario": "", "url": "https://jobs.lever.co/larian/9b21f212-a1b9-43d2-a1ef-28c783674f5b", "descripcion": "Cinematic animation", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Gameplay Animator (12 Months FTC)", "empresa": "Larian Studios", "ubicacion": "Guildford, UK", "salario": "", "url": "https://jobs.lever.co/larian/42ce1f3f-960b-467b-9481-1a04f057e62d", "descripcion": "Gameplay animation", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Character Artist", "empresa": "Larian Studios", "ubicacion": "Guildford, UK / Dublin / KL", "salario": "", "url": "https://jobs.lever.co/larian/f042d3fc-831d-4e59-977b-f4c2d687e488", "descripcion": "Character art", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "3D Environment Artist", "empresa": "Larian Studios", "ubicacion": "Guildford, UK / Dublin / KL", "salario": "", "url": "https://jobs.lever.co/larian/767cf574-55fe-45f9-a4f6-e4064b24a76d", "descripcion": "3D environment art", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Skydance Interactive (nuevos roles) ---
    {"titulo": "Senior Graphics Engineer II", "empresa": "Skydance Interactive", "ubicacion": "Los Angeles, CA", "salario": "$150k-$210k", "url": "https://jobs.lever.co/skydance/085c1161-3026-48b4-8b06-20ba0d25c601", "descripcion": "Graphics engineering UE", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Technical Director, R&D", "empresa": "Skydance Interactive", "ubicacion": "Los Angeles, CA", "salario": "$230k-$250k", "url": "https://jobs.lever.co/skydance/68a1f3cc-2475-4f66-bb7b-1cc2ba9b7002", "descripcion": "R&D Technical Director", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Animator - VR", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/171bd628-f597-47ed-87e5-deb346b1f22e", "descripcion": "Tech Animator VR", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Principal Gameplay Animator", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/78da69e1-2a2c-41e8-9b59-f09854bb3ff9", "descripcion": "Principal Gameplay Animator", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Cinematic Animator II", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "$220k-$225k", "url": "https://jobs.lever.co/skydance/ca87c796-da7d-42a1-a924-a65c44c995a2", "descripcion": "Cinematic Animator", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Animator", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/6aabc761-cecc-45ec-9453-60e3e4a20f31", "descripcion": "Gameplay Animator", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Animator 1 - VR", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "$110k-$125k", "url": "https://jobs.lever.co/skydance/86787e6e-d6ef-47bf-aaa9-32e8b02fd6fd", "descripcion": "Gameplay Animator VR", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Director", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/56de5f07-3f50-4371-9e0a-321d49a3304f", "descripcion": "Senior TD", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "CFX Senior Artist", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/28eee224-e80e-4a4e-becc-c1ed9b2b7103", "descripcion": "CFX Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Pipeline Technical Director", "empresa": "Skydance Interactive", "ubicacion": "LA/Austin/Seattle", "salario": "", "url": "https://jobs.lever.co/skydance/7756f785-baad-48b2-a8aa-67a7aacce78d", "descripcion": "Pipeline TD", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Scanline VFX ---
    {"titulo": "Unreal Generalist - Montreal", "empresa": "Scanline VFX", "ubicacion": "Montreal, Canada", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/7307501b-94ee-407d-87c9-b2a04363580f", "descripcion": "UE Generalist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Generalist - Seoul", "empresa": "Scanline VFX", "ubicacion": "Seoul, South Korea", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/dd03dd9b-faf7-4742-bd54-a3080958e420", "descripcion": "UE Generalist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Concept Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/7a6f70e1-404c-4a06-b095-067c160806bf", "descripcion": "Concept Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Environment Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/d295ec15-bef1-4762-b803-3d5307b0dbdd", "descripcion": "Environment Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "FX Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/6c1ee2e0-8c47-4ffb-b9d5-4c1c73b606ff", "descripcion": "FX Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Lead Animator", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/16b48aa8-1a16-4d3f-abac-70391231a4b8", "descripcion": "Lead Animator", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "CFX Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/2c2034b5-6e4e-4864-be5f-a17f165c2b43", "descripcion": "CFX Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Stoic Studio (REMOTE) ---
    {"titulo": "Senior 3D Environment Artist", "empresa": "Stoic Studio", "ubicacion": "Remote (Austin, TX)", "salario": "", "url": "https://jobs.lever.co/Stoic/b3dcd774-2154-41bb-ac3e-5f60791aacb8", "descripcion": "3D Environment Remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Lead 3D Character Artist", "empresa": "Stoic Studio", "ubicacion": "Remote (Austin, TX)", "salario": "", "url": "https://jobs.lever.co/Stoic/278c71b3-4c56-44d7-b092-32eb7f48f686", "descripcion": "Lead 3D Character Remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Rushdown Studios ---
    {"titulo": "Technical Director, Unreal", "empresa": "Rushdown Studios", "ubicacion": "Saratoga Springs, NY", "salario": "", "url": "https://jobs.lever.co/rushdownstudio/37c44c5e-f7c1-4608-8b78-77d42341b6a2", "descripcion": "TD Unreal", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Engineer, Unreal", "empresa": "Rushdown Studios", "ubicacion": "Saratoga Springs, NY", "salario": "", "url": "https://jobs.lever.co/rushdownstudio/8cbdfba9-600a-426e-ac11-1f0d7ed9459a", "descripcion": "Sr Gameplay Engineer UE", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Theorycraft Games (REMOTE) ---
    {"titulo": "Gameplay Engineer", "empresa": "Theorycraft Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/theorycraftgames/739fc939-59d5-41d2-aeea-0adc67ca10c4", "descripcion": "Gameplay Engineer SUPERVIVE", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Principal Gameplay Engineer", "empresa": "Theorycraft Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/theorycraftgames/efadddf6-997a-407e-87d1-2674fbed3ecb", "descripcion": "Principal Gameplay Eng", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Jagex (UE5 RuneScape) ---
    {"titulo": "Animation Programmer (UE5)", "empresa": "Jagex", "ubicacion": "Cambridge, UK", "salario": "", "url": "https://jobs.lever.co/jagex/8f3fbefe-0b7b-4185-972c-8a6f193ddfef", "descripcion": "Animation Programmer UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Artist (UE5)", "empresa": "Jagex", "ubicacion": "Cambridge, UK", "salario": "", "url": "https://jobs.lever.co/jagex/7cd40d06-f190-40e1-898d-cbc672c6b743", "descripcion": "Lead Tech Artist UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Lead Character Artist (UE5)", "empresa": "Jagex", "ubicacion": "Cambridge, UK", "salario": "", "url": "https://jobs.lever.co/jagex/ad3abc50-f565-46b5-b3b7-e627184bdc32", "descripcion": "Lead Character Artist UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Lead Environment Artist (UE5)", "empresa": "Jagex", "ubicacion": "Cambridge, UK", "salario": "", "url": "https://jobs.lever.co/jagex/c0edd5a4-5df8-429a-b425-1df76706441b", "descripcion": "Lead Environment Artist UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Creadits (REMOTE) ---
    {"titulo": "Unreal VFX Artist", "empresa": "Creadits", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/creadits/4be3f723-88b3-4ced-a9f6-8e89e45ea439", "descripcion": "VFX Artist Remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Maya/Unreal 3D Animator", "empresa": "Creadits", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/creadits/a8c972bd-c634-4596-8bec-b2044d54c114", "descripcion": "3D Animator Remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "3D Cinematic Supervisor", "empresa": "Creadits", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/creadits/dce5dd10-626f-479d-af49-a4a03411703d", "descripcion": "Cinematic Supervisor Remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Sumo Digital ---
    {"titulo": "Senior VFX Artist", "empresa": "Sumo Digital", "ubicacion": "Nottingham, UK", "salario": "", "url": "https://jobs.lever.co/sumo-digital/98b843ba-6c44-4796-a293-d6b80f1f3ca4", "descripcion": "Sr VFX Artist AAA", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Principal Technical Artist", "empresa": "Sumo Digital", "ubicacion": "Nottingham, UK", "salario": "", "url": "https://jobs.lever.co/sumo-digital/9bcca239-72e9-404a-84e3-840c8dd0dac3", "descripcion": "Principal Tech Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Kabam ---
    {"titulo": "Senior Rendering Engineer", "empresa": "Kabam", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/kabam/d81f598b-e1f6-45f1-960b-db2f2ae6aa90", "descripcion": "Rendering Engineer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior VFX Artist", "empresa": "Kabam", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://jobs.lever.co/kabam/22977388-840d-46c3-8469-7495a060bc3b", "descripcion": "Sr VFX Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Big Time Studios (FULL REMOTE) ---
    {"titulo": "Lead Gameplay Engineer - Unreal", "empresa": "Big Time Studios", "ubicacion": "Fully Remote", "salario": "", "url": "https://jobs.lever.co/bigtime/fedbbc49-c43b-4d38-8ac7-fef1765fb8f0", "descripcion": "Lead Gameplay Eng UE Remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Giant Skull (D&D game) ---
    {"titulo": "Senior Gameplay Animator", "empresa": "Giant Skull", "ubicacion": "Austin, TX", "salario": "", "url": "https://jobs.lever.co/giantskull/13326b3d-5619-4073-aedd-21f5b8740c3f", "descripcion": "Gameplay Animator D&D", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Bonfire Studios (Lever) ---
    {"titulo": "Lead Environment Artist", "empresa": "Bonfire Studios", "ubicacion": "Irvine, CA", "salario": "", "url": "https://jobs.lever.co/bonfirestudios/849b3a9f-d831-427e-8530-189eb16a0994", "descripcion": "Lead Env Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Environment Artist (Sr/Principal)", "empresa": "Bonfire Studios", "ubicacion": "Irvine, CA", "salario": "$196.5k", "url": "https://jobs.lever.co/bonfirestudios/013283f0-9206-4c28-9a2d-7fadb8f070aa", "descripcion": "Sr Environment Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Improbable ---
    {"titulo": "Sr Software Engineer - Low Level Unreal", "empresa": "Improbable", "ubicacion": "London, UK / Remote", "salario": "", "url": "https://jobs.lever.co/improbable/c2550f5e-5ee5-4cf3-9721-1ecc7cab58f4", "descripcion": "Low-level UE engineering", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Relish Studios ---
    {"titulo": "Senior Unreal Engine Developer", "empresa": "Relish Studios", "ubicacion": "Toronto, Canada", "salario": "", "url": "https://jobs.lever.co/reli-sh/f955706d-462b-4acc-9643-fdbdc7f3f521", "descripcion": "UE Dev virtual production", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Jam City ---
    {"titulo": "Senior Animator", "empresa": "Jam City", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/jamcity/b89031cd-fb1f-418e-bd10-c2a696bbcca6", "descripcion": "Sr Animator", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Opus Major (UE5 MMO) ---
    {"titulo": "Technical Game Designer (UE5)", "empresa": "Opus Major", "ubicacion": "Paris, France", "salario": "", "url": "https://jobs.lever.co/opusmajor/408ae552-3d4a-4387-a9c4-78aacb65f8da", "descripcion": "Tech Game Designer UE5 MMO", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Gameplay Programmer (UE5)", "empresa": "Opus Major", "ubicacion": "Paris, France", "salario": "", "url": "https://jobs.lever.co/opusmajor/5304392d-024b-4dcd-8741-77db973d8704", "descripcion": "Gameplay Programmer UE5 MMO", "fuente": "Lever", "fecha": "Febrero 2026"},
    # ============================================================
    # NUEVAS GREENHOUSE - Febrero 2026 sesion 2
    # ============================================================
    # --- Rockstar Games ---
    {"titulo": "Technical Artist: Animation (All Levels)", "empresa": "Rockstar Games", "ubicacion": "Leeds, UK", "salario": "", "url": "https://boards.greenhouse.io/rockstargames/jobs/4715821003", "descripcion": "Tech Artist Animation", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist (All Levels)", "empresa": "Rockstar Games", "ubicacion": "Toronto area", "salario": "", "url": "https://boards.greenhouse.io/rockstargames/jobs/4175129003", "descripcion": "Technical Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist (Mid/Senior)", "empresa": "Rockstar Games", "ubicacion": "Multiple", "salario": "", "url": "https://boards.greenhouse.io/rockstargames/jobs/5325630003", "descripcion": "Tech Artist Mid/Sr", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist: Interior Environment (All Levels)", "empresa": "Rockstar Games", "ubicacion": "Multiple", "salario": "", "url": "https://boards.greenhouse.io/rockstargames/jobs/5790200003", "descripcion": "Interior Env Tech Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist - Dynamic Art", "empresa": "Rockstar Games", "ubicacion": "Multiple", "salario": "", "url": "https://boards.greenhouse.io/rockstargames/jobs/4563785003", "descripcion": "Dynamic Art Tech Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Azra Games ---
    {"titulo": "Senior/Principal Technical Artist", "empresa": "Azra Games", "ubicacion": "Sacramento/Austin", "salario": "", "url": "https://job-boards.greenhouse.io/azragames/jobs/4348492007", "descripcion": "Sr Tech Artist RPG", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior VFX Artist", "empresa": "Azra Games", "ubicacion": "Austin, TX", "salario": "", "url": "https://job-boards.greenhouse.io/azragames/jobs/4605557007", "descripcion": "Sr VFX Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior 3D Character Artist", "empresa": "Azra Games", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/azragames/jobs/4041079007", "descripcion": "Sr 3D Character Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Sr. 3D Creature Artist", "empresa": "Azra Games", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/azragames/jobs/4510290007", "descripcion": "3D Creature Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Principal/Lead Animator", "empresa": "Azra Games", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/azragames/jobs/4510287007", "descripcion": "Lead Animator RPG", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Wargaming ---
    {"titulo": "3D Character Artist (Unannounced)", "empresa": "Wargaming", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/wargamingen/jobs/6888287", "descripcion": "3D Character Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "3D Environment Artist (WoT: HEAT)", "empresa": "Wargaming", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/wargamingen/jobs/7188959", "descripcion": "3D Env Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Level Artist (WoT: HEAT)", "empresa": "Wargaming", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/wargamingen/jobs/7573713", "descripcion": "Level Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Director (Unannounced)", "empresa": "Wargaming", "ubicacion": "Multiple", "salario": "", "url": "https://job-boards.greenhouse.io/wargamingen/jobs/6888320", "descripcion": "TD UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Highdive (NetEase - Blood Message) ---
    {"titulo": "Senior VFX Artist", "empresa": "Highdive", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/highdive/jobs/4536117007", "descripcion": "Sr VFX UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Animator", "empresa": "Highdive", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/highdive/jobs/4650517007", "descripcion": "Lead Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Cinematic Animator", "empresa": "Highdive", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/highdive/jobs/4421832007", "descripcion": "Sr Cinematic Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Character Artist", "empresa": "Highdive", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/highdive/jobs/4607865007", "descripcion": "Character Artist UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Programmer", "empresa": "Highdive", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/highdive/jobs/4548617007", "descripcion": "Sr Gameplay Programmer", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Anchor Point (NetEase) ---
    {"titulo": "VFX Artist", "empresa": "Anchor Point", "ubicacion": "Barcelona/Seattle", "salario": "", "url": "https://job-boards.greenhouse.io/anchorpoint/jobs/4682689007", "descripcion": "VFX Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Freelance Lighting Artist", "empresa": "Anchor Point", "ubicacion": "Barcelona/Seattle", "salario": "", "url": "https://job-boards.greenhouse.io/anchorpoint/jobs/4716634007", "descripcion": "Lighting Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Animator", "empresa": "Anchor Point", "ubicacion": "Barcelona/Seattle", "salario": "", "url": "https://job-boards.greenhouse.io/anchorpoint/jobs/4753896007", "descripcion": "Tech Animator", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Ghost Story Games / Take-Two (Judas) ---
    {"titulo": "Senior Environment Material Artist", "empresa": "Ghost Story Games", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/taketwo/jobs/6864945", "descripcion": "Env Material Artist Judas", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Principal 3D Artist", "empresa": "Ghost Story Games", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/taketwo/jobs/6821834", "descripcion": "Principal 3D Artist Judas", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Free Range Games (REMOTE) ---
    {"titulo": "Lead VFX Artist (Unreal)", "empresa": "Free Range Games", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/frgjobs/jobs/4390147003", "descripcion": "Lead VFX Remote UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- PUBG Seattle/Madison (KRAFTON sub) ---
    {"titulo": "Technical Artist - Lighting", "empresa": "PUBG Seattle", "ubicacion": "Bellevue, WA", "salario": "", "url": "https://job-boards.greenhouse.io/pubgseattle/jobs/7954619002", "descripcion": "Lighting Tech Artist UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Technical Artist - PCG & Worldbuilding", "empresa": "PUBG Madison", "ubicacion": "Madison, WI", "salario": "", "url": "https://job-boards.greenhouse.io/pubgmadison/jobs/7909389002", "descripcion": "PCG Worldbuilding Tech Art", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Mob Entertainment (Poppy Playtime) ---
    {"titulo": "Contract - Gameplay Programmer - Unreal & FLECS", "empresa": "Mob Entertainment", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/mobentertainment/jobs/4856224007", "descripcion": "Gameplay Programmer UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Sony Pictures Imageworks ---
    {"titulo": "Lighting Artist (Unreal)", "empresa": "Sony Pictures Imageworks", "ubicacion": "Vancouver, BC", "salario": "", "url": "https://job-boards.greenhouse.io/sonypicturesimageworks/jobs/7551004003", "descripcion": "Lighting Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Fantastic Pixel Castle (FULL REMOTE) ---
    {"titulo": "Principal Technical Animator", "empresa": "Fantastic Pixel Castle", "ubicacion": "Fully Remote", "salario": "", "url": "https://job-boards.greenhouse.io/fantasticpixelcastle/jobs/4527312007", "descripcion": "Principal Tech Animator Remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Bonfire Studios (Greenhouse) ---
    {"titulo": "Lead Environment Artist", "empresa": "Bonfire Studios", "ubicacion": "Irvine, CA", "salario": "", "url": "https://job-boards.greenhouse.io/bonfirestudiosinc/jobs/4023591009", "descripcion": "Lead Env Artist Arkheron", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Character Concept Artist (Sr/Principal)", "empresa": "Bonfire Studios", "ubicacion": "Orange County, CA", "salario": "", "url": "https://job-boards.greenhouse.io/bonfirestudiosinc/jobs/4022147009", "descripcion": "Character Concept Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- 31st Union (2K - Project ETHOS) ---
    {"titulo": "Senior VFX Artist", "empresa": "31st Union", "ubicacion": "San Mateo, CA", "salario": "", "url": "https://job-boards.greenhouse.io/31stunion/jobs/6547889003", "descripcion": "Sr VFX ETHOS", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- NetEase ---
    {"titulo": "Senior Gameplay Animator", "empresa": "NetEase Games", "ubicacion": "Montreal", "salario": "", "url": "https://job-boards.greenhouse.io/neteasegames/jobs/4556745007", "descripcion": "Gameplay Animator UE5", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # ============================================================
    # NUEVAS ASHBY - Febrero 2026 sesion 2
    # ============================================================
    # --- Believer (stylized co-op) ---
    {"titulo": "Senior VFX Artist", "empresa": "Believer", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/believer/bdb8c46a-c2a7-4571-87d6-2486e4f86214", "descripcion": "Sr VFX Artist co-op", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist", "empresa": "Believer", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/believer/1b3a3600-f8b6-4a55-ab07-bc1f52ff453e", "descripcion": "Sr Env Artist co-op", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Gameplay Engineer", "empresa": "Believer", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/believer/7e312ec3-9244-40ef-9f3c-868ebaaadb5b", "descripcion": "Gameplay Engineer", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Beyond Sports ---
    {"titulo": "Senior Unreal Developer", "empresa": "Beyond Sports", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/beyondsports/ff52df7d-cef9-41b8-b760-19ed23dbb3d8", "descripcion": "Sr UE Developer", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Gardens Interactive ---
    {"titulo": "Gameplay Engineer (Unreal 3C)", "empresa": "Gardens Interactive", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/gardens/18d46d7e-a9a4-40db-9234-df72a55b076a", "descripcion": "Gameplay Eng UE 3C", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # --- Omni Creator Products ---
    {"titulo": "Lead Environment Technical Artist", "empresa": "Omni Creator Products", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/ocp/191bb336-5556-4fb5-8a66-98e168533c77", "descripcion": "Lead Env Tech Artist", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # ============================================================
    # NUEVAS WORKABLE - Febrero 2026 sesion 2
    # ============================================================
    # --- Future House Studios (REMOTE) ---
    {"titulo": "Unreal Technical Artist", "empresa": "Future House Studios", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/future-house-studios-llc/j/0EBEEA41C2/", "descripcion": "UE Tech Artist Remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Jellyfish Pictures ---
    {"titulo": "Unreal Engine Technical Artist", "empresa": "Jellyfish Pictures", "ubicacion": "UK", "salario": "", "url": "https://apply.workable.com/jellyfish-pictures-ltd/j/E753C517A2/", "descripcion": "UE Tech Artist VFX", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Clockwork Labs ---
    {"titulo": "C/C++ Unreal Engine Developer", "empresa": "Clockwork Labs", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/clockwork-labs/j/E3991F9AA6", "descripcion": "UE Dev BitCraft MMO", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Side / Ghostpunch Games (REMOTE) ---
    {"titulo": "Contract Generalist Programmer - UE", "empresa": "Ghostpunch Games", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/sideinc/j/1545A75CAE", "descripcion": "Contract UE Programmer", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Wilder World (REMOTE) ---
    {"titulo": "Unreal 3D Generalist / Technical Artist", "empresa": "Wilder World", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/wilder-world/j/A9716D2DC2/", "descripcion": "3D Generalist UE5", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist", "empresa": "Wilder World", "ubicacion": "Remote - Europe", "salario": "", "url": "https://apply.workable.com/wilder-world/j/BB0E254230/", "descripcion": "Sr Env Artist UE5", "fuente": "Workable", "fecha": "Febrero 2026"},
    # ============================================================
    # PYTHON / HTML / WEB DEVELOPER - Chile & LATAM (Feb 2026)
    # Prioridad: Chile directo > LATAM remoto > Worldwide remoto
    # ============================================================
    # --- Lever: Bluelight Consulting (LATAM explícito) ---
    {"titulo": "Fullstack Developer (Senior) - Python Django + React", "empresa": "Bluelight Consulting", "ubicacion": "Remote, Latin America", "salario": "", "url": "https://jobs.lever.co/bluelightconsulting/4de02ce4-e528-4103-8aa8-1ee578a279a9", "descripcion": "Python Django React fullstack LATAM remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Fullstack Developer (Senior) - Python Django + React", "empresa": "Bluelight Consulting", "ubicacion": "Remote, Latin America", "salario": "", "url": "https://jobs.lever.co/bluelightconsulting/9ef76e89-7124-409f-9b54-402ef287aad7", "descripcion": "Python Django React fullstack LATAM remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Lever: Oowlish Technology (LATAM-friendly) ---
    {"titulo": "Python Developer (Airflow and Snowflake)", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/2ea0ef64-cd05-4fe7-bd63-f39a3825a6e6", "descripcion": "Python Airflow Snowflake backend", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Frontend Developer (React)", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/75b9f4e2-b644-431f-a4dc-7c886c86cb79", "descripcion": "Frontend React HTML CSS", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Full-Stack Developer (React+NodeJs)", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/167fccd0-2242-46b7-9b0f-20b518a45625", "descripcion": "Fullstack React Node web developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "JavaScript Full-Stack Developer (React/Node)", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/577287ed-093a-4c21-9922-12ba7807a623", "descripcion": "JavaScript fullstack web developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "React + Node Developer - Web Applications", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/4c434e65-7394-4aa6-8778-f7eb0fab7a2b", "descripcion": "React Node web applications", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Backend Developer - NodeJs", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/2dd4c094-b164-44e0-85e2-d27c100e7d31", "descripcion": "Backend Node.js developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Full-Stack Developer (Node & Angular)", "empresa": "Oowlish Technology", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/oowlish/35ab1541-6012-4d39-afcf-8537afef4d65", "descripcion": "Fullstack Node Angular web developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Lever: Brafton (LATAM region) ---
    {"titulo": "Remote Senior Full Stack Web Developer", "empresa": "Brafton", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/brafton/b08a103a-f067-4a79-bd18-74a86cfe9355", "descripcion": "HTML CSS SASS PHP JavaScript WordPress web developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Lever: Worldwide Remote Python ---
    {"titulo": "Senior Python Developer (100% Remote)", "empresa": "Wishpond Technologies", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/wishpond/2435df43-d3ef-4ab4-b344-d539008ce0bd", "descripcion": "Python SaaS 4+ years remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Python Backend Developer", "empresa": "JetBridge", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/JetBridge/247ff7bf-ff6e-42ee-9a31-a662a201ab73", "descripcion": "Python Django DRF backend remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Python Engineer II", "empresa": "Fliff", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/Fliff/f933b4aa-5911-490b-bb6d-c3de2994ffdc", "descripcion": "Python Django backend fully remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Python Engineer (Contract)", "empresa": "Fliff", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/Fliff/f138ece3-af0a-4a1a-9b3f-982c635f1df0", "descripcion": "Python Django contract fully remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Python Engineer (Remote)", "empresa": "Veeva Systems", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/veeva/5de877f7-1b5e-4626-a3cf-366a2ff73600", "descripcion": "Python Django 3+ years remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Frontend Engineer - React (Remote)", "empresa": "Veeva Systems", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/veeva/866d4776-9d23-4311-ab16-4ebff725984d", "descripcion": "React frontend 5+ years Python plus remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Staff Software Engineer (DevTools, Python)", "empresa": "Iterative", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/iterative/a024b3b4-d246-401a-8592-48ca24145028", "descripcion": "Python DevTools remote-first", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Software Engineer (Frontend)", "empresa": "Metabase", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/metabase/8f02d3fa-edf4-4433-a6d1-4f9e517ac8f9", "descripcion": "Frontend CSS HTML web developer remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Full Stack Developer (JavaScript + Python)", "empresa": "Smart Working Solutions", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/smart-working-solutions/9a7545b2-9d54-40e5-bd66-87be2465cc84", "descripcion": "Node.js Python fullstack 5+ years remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Full Stack Developer (Python AWS)", "empresa": "Smart Working Solutions", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/smart-working-solutions/1cc9723c-b64b-42c0-ab21-5dcb3ddc1876", "descripcion": "Python AWS Lambda microservices remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Lever: CI&T (LATAM company, Colombia) ---
    {"titulo": "Mid-Level Software Developer (Python/AWS)", "empresa": "CI&T", "ubicacion": "Colombia (LATAM)", "salario": "", "url": "https://jobs.lever.co/ciandt/ab5fbc88-0abb-423b-a678-fc4b9ebdc2ef", "descripcion": "Python AWS LATAM company", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- Lever: Chile-específicos adicionales ---
    {"titulo": "Laravel Developer + React", "empresa": "Bluelight Consulting", "ubicacion": "Santiago, Chile (Remote)", "salario": "", "url": "https://jobs.lever.co/bluelightconsulting/abd55d68-7235-4d79-b20d-acd5f6b79051", "descripcion": "Laravel React Santiago Chile web developer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "React Native Developer (LATAM Remote)", "empresa": "Bluelight Consulting", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/bluelightconsulting/eef334f8-eb67-4eae-80b2-01bafda0b400", "descripcion": "React Native mobile LATAM frontend", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Web Developer (WordPress/HTML/CSS/JS)", "empresa": "Bluelight Consulting", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://jobs.lever.co/bluelightconsulting/f3106259-ab0b-44ab-85bb-a29d9554223d", "descripcion": "HTML CSS JS WordPress web developer LATAM", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Backend Developer - Integrations", "empresa": "Yuno", "ubicacion": "Chile", "salario": "", "url": "https://jobs.lever.co/yuno/4c1ebdec-f32e-4bcf-82d4-63cc773a66db", "descripcion": "Backend developer integrations Chile", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Sr Backend Engineer - Python/Java", "empresa": "Coderio", "ubicacion": "Santiago de Chile", "salario": "", "url": "https://jobs.lever.co/coderio/3568190f-5e7a-456a-ba87-f59047f77bef", "descripcion": "Python Java backend Santiago Chile", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Backend Engineer (Python/AWS)", "empresa": "Blue Coding", "ubicacion": "LATAM (Remote)", "salario": "", "url": "https://jobs.lever.co/bluecoding/be0561bc-f9f4-4098-9650-befa416389df", "descripcion": "Python AWS backend LATAM exclusive", "fuente": "Lever", "fecha": "Febrero 2026"},
    # ============================================================
    # GREENHOUSE - Chile y LATAM Python/HTML/Web (Feb 2026)
    # ============================================================
    # --- OfferUp (Chile explícito en título, Jr Frontend) ---
    {"titulo": "Jr SDE Frontend, Services Team (@Remote, Chile)", "empresa": "OfferUp", "ubicacion": "Remote, Chile", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5944611", "descripcion": "Junior frontend React HTML CSS Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Jr SDE Frontend, Trust & Safety (@Remote, Chile)", "empresa": "OfferUp", "ubicacion": "Remote, Chile", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5752720", "descripcion": "Junior frontend React HTML CSS Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Jr SDE Frontend, Trust & Safety (@Remote, Chile/Colombia)", "empresa": "OfferUp", "ubicacion": "Remote, Chile/Colombia", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5462614", "descripcion": "Junior frontend React HTML CSS Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Jr SDE Full Stack, Ads Team (@Remote, Chile/Colombia)", "empresa": "OfferUp", "ubicacion": "Remote, Chile/Colombia", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5633157", "descripcion": "Junior fullstack React Node Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Jr SDE Backend, Explore Team (@Remote, Chile/Colombia)", "empresa": "OfferUp", "ubicacion": "Remote, Chile/Colombia", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5608107", "descripcion": "Junior backend Python Node Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Jr SDE Backend, Catalog Team (@Remote, Chile/Colombia)", "empresa": "OfferUp", "ubicacion": "Remote, Chile/Colombia", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5434810", "descripcion": "Junior backend Python Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Jr SDE Frontend, Core Team (@Remote, Chile/Colombia/CR)", "empresa": "OfferUp", "ubicacion": "Remote, Chile/Colombia/Costa Rica", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/5268848", "descripcion": "Junior frontend React HTML CSS Chile remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "SDE II - Frontend, Services Team", "empresa": "OfferUp", "ubicacion": "Remote, Chile", "salario": "", "url": "https://boards.greenhouse.io/offerup/jobs/7438212", "descripcion": "Mid frontend React Chile explicit", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Sezzle (LATAM Junior!) ---
    {"titulo": "Junior Software Engineer (LATAM)", "empresa": "Sezzle", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/sezzle/jobs/5761145003", "descripcion": "Junior software engineer Python LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Junior Software Engineer w/ Accounting (LATAM)", "empresa": "Sezzle", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/sezzle/jobs/6668065003", "descripcion": "Junior software engineer accounting LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Nearsure (LATAM Python/Frontend) ---
    {"titulo": "Senior Backend Python Developer", "empresa": "Nearsure", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/nearsure/jobs/4599601007", "descripcion": "Senior Python backend LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Semi Senior Fullstack Python Engineer", "empresa": "Nearsure", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/nearsure/jobs/4339105007", "descripcion": "Semi senior Python fullstack LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Frontend Web Developer", "empresa": "Nearsure", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/nearsure/jobs/4523308007", "descripcion": "Senior frontend web HTML CSS LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Software Engineer Python", "empresa": "Nearsure", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/nearsure/jobs/4518538007", "descripcion": "Senior Python software engineer LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Otros LATAM Greenhouse ---
    {"titulo": "Python Cloud Engineer", "empresa": "Admios", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/admios/jobs/5751446002", "descripcion": "Python cloud engineer LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "React Frontend Engineer (LATAM)", "empresa": "VidMob", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/vidmob/jobs/4924012003", "descripcion": "React frontend HTML CSS LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Software Engineer (Python) - LATAM", "empresa": "OfferFit", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/offerfit/jobs/4446093005", "descripcion": "Python software engineer LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "LATAM Principal Software Engineer (Python/Go)", "empresa": "Praxent", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/praxent/jobs/6267215003", "descripcion": "Principal Python Go LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Data Engineer (Python) - LATAM", "empresa": "Truelogic", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/truelogic/jobs/7449241002", "descripcion": "Data engineer Python LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Frontend Engineer - Open Platform", "empresa": "Yalo Inc.", "ubicacion": "LATAM Remote", "salario": "", "url": "https://boards.greenhouse.io/yalochatinc/jobs/6656262003", "descripcion": "Frontend engineer HTML CSS LATAM", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Talent Pool (Chile)", "empresa": "Teampathy", "ubicacion": "Chile", "salario": "", "url": "https://boards.greenhouse.io/teampathy/jobs/4618167008", "descripcion": "Talent pool Chile developers", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Greenhouse Worldwide Remote Python/Web ---
    {"titulo": "Web Frontend Engineer (JS, CSS, React, Flutter)", "empresa": "Canonical", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://boards.greenhouse.io/canonicaljobs/jobs/7131511", "descripcion": "Frontend web CSS React Flutter global remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Software Engineer (Work from Anywhere)", "empresa": "Xapo Bank", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://boards.greenhouse.io/xapo61/jobs/7572065003", "descripcion": "Software engineer work from anywhere Python", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Front-End Web Developer (Work from Anywhere)", "empresa": "Xapo Bank", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://boards.greenhouse.io/xapo61/jobs/7580805003", "descripcion": "Frontend web developer HTML CSS anywhere", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- Workable: Stack Builders LATAM ---
    {"titulo": "Full-Stack React + Python Developer (Remote LATAM)", "empresa": "Stack Builders", "ubicacion": "Remote, LATAM", "salario": "", "url": "https://apply.workable.com/stackbuilders/j/F58A1270A0", "descripcion": "React Python fullstack LATAM remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    # --- Ashby: Deel (opera en Chile) ---
    {"titulo": "Front-End Engineer LATAM", "empresa": "Deel", "ubicacion": "LATAM Remote", "salario": "", "url": "https://jobs.ashbyhq.com/deel/bb349fda-7b81-48c2-aabe-c1990999d648", "descripcion": "Frontend engineer HTML CSS LATAM Deel", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Full-Stack Engineer LATAM", "empresa": "Deel", "ubicacion": "LATAM Remote", "salario": "", "url": "https://jobs.ashbyhq.com/deel/87c5dc9f-6610-47da-9ca1-40ef5730c5bb", "descripcion": "Fullstack engineer Python LATAM Deel", "fuente": "Ashby", "fecha": "Febrero 2026"},

    # ============================================================
    # NUEVAS OFERTAS - 14 Feb 2026 (Busqueda automatizada)
    # ============================================================

    # --- LEVER: Game Studios UE/Programming ---
    {"titulo": "Senior Unreal Engineer (PC & Mobile)", "empresa": "Demiurge Studios", "ubicacion": "Remote-friendly", "salario": "", "url": "https://jobs.lever.co/demiurgestudios/7678dbef-8d30-49a2-a5b2-22086cfc9a52", "descripcion": "Sr UE Engineer PC Mobile", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Unreal Engineer (PC & Console)", "empresa": "Demiurge Studios", "ubicacion": "Remote-friendly", "salario": "", "url": "https://jobs.lever.co/demiurgestudios/1e2ab28c-19c5-42a0-a9a8-9923e83c769e", "descripcion": "Sr UE Engineer PC Console", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "2026 Associate Software Engineer", "empresa": "Demiurge Studios", "ubicacion": "Remote-friendly", "salario": "", "url": "https://jobs.lever.co/demiurgestudios/f178d670-83a0-49e6-a98a-5d86afb42366", "descripcion": "Assoc SE 2026", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Software Engineer (PC)", "empresa": "Demiurge Studios", "ubicacion": "Remote-friendly", "salario": "", "url": "https://jobs.lever.co/demiurgestudios/3db6a314-9731-4deb-ac1e-cf4ab2648cd0", "descripcion": "Sr SE PC games", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "UI/UX Artist", "empresa": "Demiurge Studios", "ubicacion": "Remote-friendly", "salario": "", "url": "https://jobs.lever.co/demiurgestudios/5081cd40-a956-406a-ad72-05452cb62f79", "descripcion": "UI UX Artist games", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Engine C++ Software Engineer", "empresa": "ZURU", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/zuru/a2b16d6f-4798-447d-98aa-21c972598c63", "descripcion": "UE C++ SE", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Game Designer UE", "empresa": "Seedify", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/seedify-fund/79204716-6b36-490a-9f49-b769c393c001", "descripcion": "Sr Game Designer UE large maps", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Game Developer UE", "empresa": "Gravis Robotics", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/gravisrobotics/ea0246d5-aa57-4c18-8416-730fe3e6e1e1", "descripcion": "Game Dev UE gamified control", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "VR Teleoperation UI/UX Engineer", "empresa": "Toyota Research Institute", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/tri/3e8c1036-eb6b-4270-a435-3ddafd0cb384", "descripcion": "VR UI UX Unity Unreal", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Gameplay Engineer UE5", "empresa": "Stoic Studio", "ubicacion": "Fully Remote", "salario": "", "url": "https://jobs.lever.co/Stoic/7f62308e-340d-4c9f-bc7c-10f0cd6dadac", "descripcion": "Sr Gameplay Eng UE5 remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "DevOps Engineer UE5", "empresa": "Stoic Studio", "ubicacion": "Fully Remote", "salario": "", "url": "https://jobs.lever.co/Stoic/96d77027-03ab-4a59-9602-1a5e88c4790b", "descripcion": "DevOps UE5 multiplayer remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- LEVER: Art / VFX / Character ---
    {"titulo": "Environment Artist (10mo Contract)", "empresa": "Blackbird Interactive", "ubicacion": "Remote Canada", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/4547eed2-3efc-4074-afe6-d289918052f9", "descripcion": "Env Artist UE5 contract", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "3D Character Artist", "empresa": "Blackbird Interactive", "ubicacion": "Remote Canada", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/e4bfa404-ab09-4652-9f58-034c2e9fa895", "descripcion": "3D Char Artist UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist - Lookdev (Contract)", "empresa": "Blackbird Interactive", "ubicacion": "Remote Canada", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/51f9914e-8d50-4d56-a118-24181b59e684", "descripcion": "Tech Artist shaders materials lighting", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Technical UI Artist", "empresa": "Blackbird Interactive", "ubicacion": "Remote Canada", "salario": "", "url": "https://jobs.lever.co/blackbirdinteractive/1bb42134-286c-40a5-8543-c5f28788e3ff", "descripcion": "Tech UI Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior VFX Artist", "empresa": "Wildlight Entertainment", "ubicacion": "Remote US/Canada", "salario": "", "url": "https://jobs.lever.co/wildlight/c91bfcd3-654b-45b4-b388-e38aeea249fe", "descripcion": "Sr VFX Artist remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Principal Lighting Artist UE5", "empresa": "Giant Skull", "ubicacion": "Hybrid/Remote", "salario": "", "url": "https://jobs.lever.co/giantskull/68e760d1-b711-4ad2-a265-0e76502a9685", "descripcion": "Principal Lighting UE5 D&D", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior 3D Environment Artist", "empresa": "Big Time", "ubicacion": "Fully Remote Worldwide", "salario": "", "url": "https://jobs.lever.co/bigtime/41a9ce8a-77b1-4727-bb10-2ef0e521cbd6", "descripcion": "Sr 3D Env Artist remote worldwide", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist (Vanguard)", "empresa": "Remedy Entertainment", "ubicacion": "Finland/Remote", "salario": "", "url": "https://jobs.lever.co/remedyentertainment/bd57ba05-b1b5-440c-9986-066a22e36844", "descripcion": "Sr Env Artist Remedy Vanguard", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Environment Artist", "empresa": "Crytek", "ubicacion": "Frankfurt/Remote", "salario": "", "url": "https://jobs.lever.co/crytek/b1368379-5d32-477f-bf74-0fadf2d343e5", "descripcion": "Env Artist Crytek", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Character Artist UE", "empresa": "Cryptic Studios", "ubicacion": "Remote US", "salario": "", "url": "https://jobs.lever.co/crypticstudios/833e2427-ada5-4c3e-b144-9b5fbb879af5", "descripcion": "Sr Char Artist UE remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Open World Level Designer UE5", "empresa": "Cryptic Studios", "ubicacion": "Remote US", "salario": "", "url": "https://jobs.lever.co/crypticstudios/41402a43-0249-4b15-a09f-1b139a599457", "descripcion": "Sr Open World LD UE5", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Character Concept Artist (Principal/Senior)", "empresa": "Bonfire Studios", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/bonfirestudios/63e0c723-4e49-4aff-a805-ee58251d700d", "descripcion": "Char Concept Artist AAA", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Character Concept Artist AAA", "empresa": "Sumo/Atomhawk", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/sumo-digital/d91a0f64-02fa-4e50-9a72-aa8cc32e4b7e", "descripcion": "Char Concept Artist AAA remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Concept Artist AAA", "empresa": "Sumo/Atomhawk", "ubicacion": "Remote PST", "salario": "", "url": "https://jobs.lever.co/sumo-digital/bab9c709-eb78-42bb-9b9d-486bc374c186", "descripcion": "Concept Artist AAA remote", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Game Artist - Midcore", "empresa": "Voodoo", "ubicacion": "Fully Remote", "salario": "", "url": "https://jobs.lever.co/voodoo/7810d528-6cb0-436f-bf0d-851c1d6083f5", "descripcion": "Sr Game Artist midcore", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Artist", "empresa": "Kabam", "ubicacion": "Vancouver", "salario": "", "url": "https://jobs.lever.co/kabam/1ddad459-0ae1-4ae7-bafb-d43f95b72ffc", "descripcion": "Sr Tech Artist Kabam", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist Tools/Pipelines", "empresa": "Playco", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/playco/5b5e4788-8dcd-4000-8153-19e8ff0bf59c", "descripcion": "Tech Artist tools pipelines", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "3D Character Artist", "empresa": "Convai", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/Convai-technologies-inc/2d85a7fe-c363-462d-b45a-160f4cf2413e", "descripcion": "3D Char Artist AI", "fuente": "Lever", "fecha": "Febrero 2026"},
    # --- LEVER: Skydance/Scanline/MomentFactory nuevos UUIDs ---
    {"titulo": "Sr Gameplay Animator", "empresa": "Skydance", "ubicacion": "LA/Remote", "salario": "", "url": "https://jobs.lever.co/skydance/6aabc761-cecc-45ec-9453-60e3e4a20f31", "descripcion": "Sr Gameplay Animator", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Sr Software Engineer UE", "empresa": "Skydance", "ubicacion": "LA/Remote", "salario": "", "url": "https://jobs.lever.co/skydance/fcca7874-3162-4262-9f1c-0961b7ca4900", "descripcion": "Sr SE Unreal Engine", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Technical Director R&D", "empresa": "Skydance", "ubicacion": "LA/Remote", "salario": "", "url": "https://jobs.lever.co/skydance/68a1f3cc-2475-4f66-bb7b-1cc2ba9b7002", "descripcion": "Tech Director R&D", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Generalist VFX", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/d42f02f7-8ebf-4d84-833f-20771ae89e05", "descripcion": "Generalist VFX", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Animator", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/d50a4041-0bc3-401a-9ada-78d65f577485", "descripcion": "Animator VFX", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "FX Artist Montreal", "empresa": "Scanline VFX", "ubicacion": "Montreal", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/6a47a9f4-751a-4bb3-8ad0-f04159389e2f", "descripcion": "FX Artist Montreal", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior FX Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/e9d69baa-fa18-40f5-b215-52203375c0ef", "descripcion": "Sr FX Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior FX Artist London", "empresa": "Scanline VFX", "ubicacion": "London", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/32857644-de76-448e-b713-e9891e124778", "descripcion": "Sr FX Artist London", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Visual Pioneering Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/82a1bd63-61e9-4eea-8af0-030ab4e8f6d5", "descripcion": "Visual Pioneering Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "CFX Artist", "empresa": "Scanline VFX", "ubicacion": "Multiple", "salario": "", "url": "https://jobs.lever.co/scanlinevfx/8648d411-fa12-4459-8336-a9e5917899c3", "descripcion": "CFX Artist", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Interactive Designer", "empresa": "Moment Factory", "ubicacion": "Montreal", "salario": "", "url": "https://jobs.lever.co/momentfactory/2b2900cd-d751-4931-9214-48344fa735eb", "descripcion": "Interactive Designer", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Creative Director Themed Entertainment", "empresa": "Moment Factory", "ubicacion": "Montreal", "salario": "", "url": "https://jobs.lever.co/momentfactory/f936b9d3-4c9f-4954-a851-40e18a0bf1c3", "descripcion": "Creative Dir themed", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Creative Director", "empresa": "Moment Factory", "ubicacion": "Montreal", "salario": "", "url": "https://jobs.lever.co/momentfactory/089ed8bc-3c56-4e8e-be4c-65a8d008098c", "descripcion": "Creative Director", "fuente": "Lever", "fecha": "Febrero 2026"},

    # --- GREENHOUSE: Python + Pipeline (ALTA PRIORIDAD) ---
    {"titulo": "Technical Artist (Python + UE Pipeline)", "empresa": "BulletFarm", "ubicacion": "Remote NA", "salario": "", "url": "https://boards.greenhouse.io/bulletfarm/jobs/4360857007", "descripcion": "Tech Artist Python C# UE pipeline", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Python Developer - Game Tools & Content", "empresa": "NVIDIA (via Sustainable Talent)", "ubicacion": "Remote", "salario": "$65-$90/hr", "url": "https://boards.greenhouse.io/sustainabletalent/jobs/4594536005", "descripcion": "Python game tools content systems", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Python SE - 2D/3D Content and UI", "empresa": "NVIDIA (via Sustainable Talent)", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/sustainabletalent/jobs/4315593005", "descripcion": "Python 2D 3D content UI", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Python Developer - Game Tools", "empresa": "Rockstar Games", "ubicacion": "Multiple", "salario": "", "url": "https://boards.greenhouse.io/rockstargames/jobs/4386223003", "descripcion": "Python dev game tools pipeline", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "UE Technical Artist (Python + C++ + BP)", "empresa": "MrBeast", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/mrbeastyoutube/jobs/4800773004", "descripcion": "UE Tech Artist Python C++ Blueprints", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Pipeline Technical Animator", "empresa": "Cloud Chamber", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/cloudchamberen/jobs/5790524003", "descripcion": "Sr Pipeline Tech Animator Python DCC UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Artist - UE", "empresa": "PUBG Madison", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/pubgmadison/jobs/5403975002", "descripcion": "Sr Tech Artist UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- GREENHOUSE: Environment / Character / Materials ---
    {"titulo": "Senior 3D Environment Artist", "empresa": "PlayQ", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/playq/jobs/3255590", "descripcion": "Sr 3D Env Artist remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist", "empresa": "Sony Bend", "ubicacion": "Fully Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4241234004", "descripcion": "Sr Env Artist Sony Bend remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Materials Artist", "empresa": "Cloud Chamber", "ubicacion": "Fully Remote US", "salario": "", "url": "https://boards.greenhouse.io/cloudchamberen/jobs/6000950003", "descripcion": "Sr Materials Artist BioShock UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist", "empresa": "Unknown Worlds", "ubicacion": "Fully Remote", "salario": "", "url": "https://boards.greenhouse.io/unknownworlds/jobs/7868047002", "descripcion": "Sr Env Artist distributed remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist (Unannounced)", "empresa": "ArenaNet", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/arenanet/jobs/4666070", "descripcion": "Sr Env Artist unannounced", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "3D Artist", "empresa": "Mythical Games", "ubicacion": "Remote US", "salario": "", "url": "https://boards.greenhouse.io/mythicalgames/jobs/4774774003", "descripcion": "3D Artist remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Intermediate Environment Artist", "empresa": "Digital Extremes", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/digitalextremes/jobs/4530388007", "descripcion": "Int Env Artist remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate Environment Artist", "empresa": "Bungie", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/bungie/jobs/4710229", "descripcion": "Assoc Env Artist digital-first", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead Environment Artist", "empresa": "PlayStation", "ubicacion": "US Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4306065004", "descripcion": "Lead Env Artist US remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Texture/Material Artist", "empresa": "Level Ex", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/levelex/jobs/4764726003", "descripcion": "Texture Material Artist contract", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- GREENHOUSE: Technical Artist ---
    {"titulo": "Technical Artist WWE 2K", "empresa": "Visual Concepts", "ubicacion": "Fully Remote US", "salario": "$41-$58/hr", "url": "https://boards.greenhouse.io/visualconcepts/jobs/4194737003", "descripcion": "Tech Artist WWE 2K remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist", "empresa": "1047 Games", "ubicacion": "Permanently Remote", "salario": "", "url": "https://boards.greenhouse.io/1047games/jobs/4331272004", "descripcion": "Tech Artist permanently remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Technical Artist (Unannounced)", "empresa": "PlayStation", "ubicacion": "Fully Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4464647004", "descripcion": "Sr Tech Artist unannounced remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Procedural Technical Artist (Unannounced)", "empresa": "PlayStation", "ubicacion": "Fully Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4498354004", "descripcion": "Procedural Tech Artist Houdini UE", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Technical Artist HLSL/UE", "empresa": "SuperNatural Studios", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/supernaturalstudios/jobs/4086755005", "descripcion": "Tech Artist HLSL UE shading tools", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- GREENHOUSE: VFX / Lighting ---
    {"titulo": "Senior Lighting Artist UE5", "empresa": "PUBG Madison", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/pubgmadison/jobs/8130469002", "descripcion": "Sr Lighting Artist UE5 Lumen", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Real-Time VFX Artist", "empresa": "Digital Extremes", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/digitalextremes/jobs/4119092007", "descripcion": "Sr RT VFX Artist remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Lighting Artist UE5 Lumen", "empresa": "Bit Reactor", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/bitreactor/jobs/5129816004", "descripcion": "Sr Lighting Artist UE5 Lumen", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "VFX Artist (Associate-Mid)", "empresa": "Bungie", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/bungie/jobs/2666429", "descripcion": "VFX Artist digital-first remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "VFX Artist", "empresa": "Firaxis", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/firaxis/jobs/5328892003", "descripcion": "VFX Artist Firaxis", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "VFX Artist", "empresa": "Digital Extremes", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/digitalextremes/jobs/4638694007", "descripcion": "VFX Artist remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead VFX Artist", "empresa": "Cloud Chamber", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/cloudchamberen/jobs/4669849003", "descripcion": "Lead VFX Artist BioShock", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Destiny Senior VFX Artist", "empresa": "Bungie", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/bungie/jobs/4740262", "descripcion": "Sr VFX Artist Destiny remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # --- GREENHOUSE: Character / Concept ---
    {"titulo": "Lead Character Artist", "empresa": "Insomniac", "ubicacion": "Remote US", "salario": "", "url": "https://boards.greenhouse.io/insomniac/jobs/5200598004", "descripcion": "Lead Char Artist remote", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Concept Artist", "empresa": "Bit Reactor", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/bitreactor/jobs/4342805004", "descripcion": "Sr Concept Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Concept Artist", "empresa": "Bit Reactor", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/bitreactor/jobs/4460040004", "descripcion": "Concept Artist", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Character Artist (Contract)", "empresa": "PlayStation", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4245905004", "descripcion": "Sr Char Artist contract", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior Character Artist (UE MetaHuman)", "empresa": "Wevr", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/wevr/jobs/4301856004", "descripcion": "Sr Char Artist UE MetaHuman", "fuente": "Greenhouse", "fecha": "Febrero 2026"},

    # --- WORKABLE: Nuevas ---
    {"titulo": "Associate VFX Artist", "empresa": "Escape Velocity", "ubicacion": "Remote NA/CA/EU", "salario": "", "url": "https://apply.workable.com/escape-velocity-entertainment-inc/j/4E91BFE49F/", "descripcion": "Assoc VFX Artist remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist UE5", "empresa": "Wilder World", "ubicacion": "Remote EU", "salario": "", "url": "https://apply.workable.com/wilder-world/j/BB0E254230/", "descripcion": "Sr Env Artist UE5 remote EU", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist VR", "empresa": "nDreams", "ubicacion": "Remote UK", "salario": "", "url": "https://apply.workable.com/ndreams/j/7786704660/", "descripcion": "Sr Env Artist VR UE remote UK", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "VFX Artist VR", "empresa": "nDreams", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/ndreams/j/AFEC4CEBE6/", "descripcion": "VFX Artist VR games", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Artist - Orbital", "empresa": "nDreams", "ubicacion": "Fully Remote", "salario": "", "url": "https://apply.workable.com/ndreams/j/D6760E4187/", "descripcion": "Sr Artist Orbital fully remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "3D Environment/Props Artist FPS AAA", "empresa": "Sperasoft", "ubicacion": "Poland/Remote", "salario": "", "url": "https://apply.workable.com/sperasoft/j/3A2086DFE2", "descripcion": "3D Env Props Artist FPS AAA", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "3D Environment Artist Talent Pool", "empresa": "Side/PTW", "ubicacion": "N Americas", "salario": "", "url": "https://apply.workable.com/sideinc/j/4F9ABDA3E7/", "descripcion": "3D Env Artist talent pool", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Lead Artist / 3D Character Artist", "empresa": "PTW", "ubicacion": "UK Remote", "salario": "", "url": "https://apply.workable.com/ptw-i/j/2D071E01FA/", "descripcion": "Lead 3D Char Artist UK", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Junior Level Animator", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/068E130D6B", "descripcion": "Jr Animator remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Lead Animator", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/CE2A226781", "descripcion": "Lead Animator remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Concept Artist", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/AB085E4D2C", "descripcion": "Concept Artist remote", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Game VFX Artist", "empresa": "Side/PTW", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/sideinc/j/F1B5DEE0A2/", "descripcion": "Game VFX Artist", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "UI/UX Designer (UE & Unity)", "empresa": "Devoted Studios", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/devoted-studios-1/j/6F766747FC", "descripcion": "UI UX Designer UE Unity", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Network Python Developer", "empresa": "Cyrex/Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/cyrex/j/5F11495FFB", "descripcion": "Network Python Dev games", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Backend Python Engineer Gaming", "empresa": "Tripledot Studios", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/tripledotstudios/j/C563D9E4E6/", "descripcion": "Backend Python gaming", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "3D Game Artist OSRS", "empresa": "Jagex", "ubicacion": "Remote UK", "salario": "", "url": "https://apply.workable.com/jagex-limited/j/5CEED2CA01", "descripcion": "3D Game Artist OSRS FTC", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Python Developer & AI", "empresa": "Workstate", "ubicacion": "CO Remote", "salario": "", "url": "https://apply.workable.com/workstate/j/8BB60CF32A", "descripcion": "Sr Python Dev AI integrator", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Engine Artist", "empresa": "Unreal Gigs", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/unreal-gigs/j/9A7E7F2CC0/", "descripcion": "UE Artist", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Technical Artist", "empresa": "Unreal Gigs", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/unreal-gigs/j/F179209689/", "descripcion": "UE Tech Artist", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Engine Developer Remote", "empresa": "Jobgether", "ubicacion": "Remote Anywhere", "salario": "", "url": "https://apply.workable.com/jobgether/j/5821616FA5/", "descripcion": "UE Developer remote anywhere", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior 3D Artist Casual Games", "empresa": "Homa Games", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/homa-games/j/CA53F31383", "descripcion": "Sr 3D Artist casual", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior 3D/2D Game Artist", "empresa": "Homa Games", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/homa-games/j/51147D9FFF", "descripcion": "Sr 3D 2D Game Artist", "fuente": "Workable", "fecha": "Febrero 2026"},

    # --- ASHBY: Nuevas ---
    {"titulo": "3D Artist Mobile", "empresa": "HyperHug", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/hyperhug/81b041a1-1a2a-4c34-b0f7-b38ad56ef003", "descripcion": "3D Artist mobile shooter", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Senior 3D Artist", "empresa": "HyperHug", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/hyperhug/0e3fb050-d380-4b4d-9d61-ea266721a1fc", "descripcion": "Sr 3D Artist", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "3D Environment Artist", "empresa": "Millions of Monsters", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/monsters/f42f3f30-2e92-46e6-bfe7-9f15f10a94af", "descripcion": "3D Env Artist", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "3D Environmental Artist", "empresa": "Super Evil Megacorp", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/superevilmegacorp/041e9894-d0a8-4620-84ae-0c09098d0906", "descripcion": "3D Env Artist", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Senior Environment Artist VR", "empresa": "Greensky Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/greenskygames/4ed594fb-4146-4e53-9d94-727ea1db63a5", "descripcion": "Sr Env Artist VR", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "3D Artist", "empresa": "Greensky Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/greenskygames/29ab808f-8891-4919-8707-961a3c8201d8", "descripcion": "3D Artist VR", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Staff Technical Artist", "empresa": "Genesis AI", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/genesis-ai/56c4f858-8b99-4f73-affe-fd96c8ab73df", "descripcion": "Staff Tech Artist remote", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Environment Artist Senior+", "empresa": "Omni Creator Products", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/ocp/e3e08882-8855-434d-9a91-1f7dcee8af14", "descripcion": "Env Artist Sr+", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Engine UI Programmer", "empresa": "thatgamecompany", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/thatgamecompany/e709635b-77a3-4713-882a-caea0e939672", "descripcion": "Engine UI Programmer", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Technical Game Designer", "empresa": "thatgamecompany", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/thatgamecompany/22deed1d-6098-45eb-a04d-41634b23ec30", "descripcion": "Tech Game Designer", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Game Artist Puzzle Games", "empresa": "Voodoo", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/voodoo/500cf609-da11-4f5d-a701-b2b1ddcdcead", "descripcion": "Game Artist puzzle", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Game Developer Portfolio Games", "empresa": "Voodoo", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/voodoo/465a1b6e-9488-4079-93b5-093c8829a4fa", "descripcion": "Game Dev portfolio", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Senior Game Developer UE5", "empresa": "Pixaera", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/pixaera/334f2067-2363-4a2e-8d26-0a2ef7c7c4d4", "descripcion": "Sr Game Dev UE5 safety", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Unreal Gameplay Programmer UEFN", "empresa": "Worlds", "ubicacion": "Remote Worldwide", "salario": "", "url": "https://jobs.ashbyhq.com/Worlds/901c8df2-3893-4113-9c1a-6f171bb400d3", "descripcion": "UE Gameplay Prog UEFN Verse", "fuente": "Ashby", "fecha": "Febrero 2026"},
    # === QA / GAME TESTING - Febrero 2026 ===
    # Greenhouse QA
    {"titulo": "Senior QA Tester", "empresa": "Unknown Worlds", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/unknownworlds/jobs/7675845002", "descripcion": "Senior QA Tester Subnautica", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Remote Game Test Analyst - PSSQA", "empresa": "PlayStation", "ubicacion": "Remote US", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4731921004", "descripcion": "Game Test Analyst PlayStation", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Game Test Analyst - Live Services", "empresa": "PlayStation", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4586424004", "descripcion": "Game Test Analyst Live Services", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Game Test Analyst - PSSQA", "empresa": "PlayStation", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4242196004", "descripcion": "Game Test Analyst PSSQA", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester - Mobile Games", "empresa": "Cat Daddy", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/catdaddy/jobs/5077050003", "descripcion": "QA Tester mobile games", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester (Temporary)", "empresa": "2K Vegas", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/2kvegas/jobs/5888179003", "descripcion": "QA Tester temp 2K", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester - Analytics", "empresa": "2K Vegas", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/2kvegas/jobs/5206557003", "descripcion": "QA Tester analytics 2K", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Lead QA Analyst", "empresa": "ArenaNet", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/arenanet/jobs/3883641", "descripcion": "Lead QA Analyst ArenaNet", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester", "empresa": "ArenaNet", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/arenanet/jobs/5505643", "descripcion": "QA Tester ArenaNet", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Senior QA Analyst - Environments", "empresa": "Hypixel Studios", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/hypixelstudios/jobs/5908159003", "descripcion": "Senior QA Analyst Environments Hypixel", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst - Instant Games", "empresa": "MobilityWare", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/mobilityware/jobs/1714200", "descripcion": "QA Analyst Instant Games", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst", "empresa": "Epic Games", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/epicgames/jobs/5591183004", "descripcion": "QA Analyst Epic Games", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst", "empresa": "Wargaming", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/wargamingen/jobs/3306929", "descripcion": "QA Analyst Wargaming", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Web & API QA Tester", "empresa": "PlayStation", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/5184136004", "descripcion": "Web API QA Tester PlayStation", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Development QA Tester", "empresa": "PlayStation", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/sonyinteractiveentertainmentglobal/jobs/4935231004", "descripcion": "Development QA Tester PlayStation", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate QA Tester (German)", "empresa": "Naughty Dog", "ubicacion": "Remote US", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5676715004", "descripcion": "Associate QA Tester German Naughty Dog", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate QA Tester (Korean)", "empresa": "Naughty Dog", "ubicacion": "Remote US", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5710884004", "descripcion": "Associate QA Tester Korean Naughty Dog", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate QA Tester (Italian)", "empresa": "Naughty Dog", "ubicacion": "Remote US", "salario": "", "url": "https://job-boards.greenhouse.io/naughtydog/jobs/5676721004", "descripcion": "Associate QA Tester Italian Naughty Dog", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Game Development QA Tester", "empresa": "Tripwire Interactive", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/tripwireinteractive/jobs/7739553002", "descripcion": "Game Dev QA Tester Tripwire", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Manager - Unannounced Project", "empresa": "Scopely", "ubicacion": "Remote EU", "salario": "", "url": "https://job-boards.greenhouse.io/scopely/jobs/5112022008", "descripcion": "QA Manager Scopely", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst Networking/Multiplayer", "empresa": "Turtle Rock Studios", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/turtlerockstudios/jobs/4468423005", "descripcion": "QA Analyst Multiplayer Turtle Rock", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate QA Tester Online Services", "empresa": "Rockstar Games", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/rockstargames/jobs/6089977003", "descripcion": "Assoc QA Tester Online Rockstar", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Contract Generalist Tester Destiny 2", "empresa": "Bungie", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/bungie/jobs/7235937", "descripcion": "Contract Tester Destiny 2 Bungie", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate QA Tester Game Functionality", "empresa": "Rockstar Games", "ubicacion": "Remote", "salario": "", "url": "https://job-boards.greenhouse.io/rockstargames/jobs/5885793003", "descripcion": "Assoc QA Tester Rockstar", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate Audio QA Analyst", "empresa": "Epic Games", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/epicgames/jobs/4319396004", "descripcion": "Audio QA Analyst Epic", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "Associate QA Analyst", "empresa": "Thats No Moon", "ubicacion": "Remote / LA", "salario": "", "url": "https://boards.greenhouse.io/thatsnomoonentertainment/jobs/5204994004", "descripcion": "Assoc QA Analyst Thats No Moon", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst - Interoperability", "empresa": "Twinmotion", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/twinmotion/jobs/4179321004", "descripcion": "QA Analyst Twinmotion", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Lead Analyst", "empresa": "NCSOFT", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/ncsoftwest/jobs/2293076", "descripcion": "QA Lead NCSOFT", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst (Temp)", "empresa": "Pocket Gems", "ubicacion": "Remote", "salario": "", "url": "https://boards.greenhouse.io/pocketgems/jobs/3043710", "descripcion": "QA Analyst temp Pocket Gems", "fuente": "Greenhouse", "fecha": "Febrero 2026"},
    # Lever QA
    {"titulo": "QA Tester (Contract)", "empresa": "Mountaintop Studios", "ubicacion": "Remote US", "salario": "", "url": "https://jobs.lever.co/mountaintop/3130d5f9-18c8-40fb-a544-61f9461ba51a", "descripcion": "QA Tester contract Mountaintop", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior Automation Tester", "empresa": "Magnopus", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/magnopus/9ef2a0ef-f600-4623-a648-6520cca6baec", "descripcion": "Sr Automation Tester Magnopus", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst II", "empresa": "Super.com", "ubicacion": "Remote Global", "salario": "", "url": "https://jobs.lever.co/super-com/8f73d67e-b7b9-41e8-a9ce-23ee39fbb4ef", "descripcion": "QA Analyst II Super.com", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst", "empresa": "Jam City", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/jamcity/f0340e34-b176-4048-b46c-b69e1500787d", "descripcion": "QA Analyst Jam City", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst JR", "empresa": "Jam City", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/jamcity/9b5ac298-b57f-4df3-acbf-5234c2c49c2c", "descripcion": "QA Analyst JR Jam City", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst (Publishing)", "empresa": "Neowiz", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/neowiz/2b448a1c-ab01-4f07-8260-d90b8086f9e9", "descripcion": "QA Analyst Publishing Neowiz", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Principal QA Analyst", "empresa": "Kabam", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/kabam/46be7128-019d-4e19-a05d-7fdb962d8d60", "descripcion": "Principal QA Analyst Kabam", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Senior QA Analyst (Remote US)", "empresa": "Age of Learning", "ubicacion": "Remote US", "salario": "", "url": "https://jobs.lever.co/aofl/a70c10a2-d347-4e3e-96dc-da747ab2daa6", "descripcion": "Sr QA Analyst Age of Learning", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "Manual QA Tester - Mobile", "empresa": "Jobgether", "ubicacion": "Remote US", "salario": "", "url": "https://jobs.lever.co/jobgether/c88222cc-6045-49e0-9f63-aa4b4780b7f1", "descripcion": "Manual QA Tester Mobile", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst/Manual Tester (Remote)", "empresa": "Topaz Labs", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/topazlabs/463053a5-e30f-429d-941f-5b37404f695d", "descripcion": "QA Analyst Manual Tester Topaz", "fuente": "Lever", "fecha": "Febrero 2026"},
    {"titulo": "SDET Gaming Industry", "empresa": "Smart Working Solutions", "ubicacion": "Remote", "salario": "", "url": "https://jobs.lever.co/smart-working-solutions/7a96b32c-4747-43c8-a822-2d251f1dd997", "descripcion": "SDET Gaming Smart Working", "fuente": "Lever", "fecha": "Febrero 2026"},
    # Workable QA
    {"titulo": "QA Game Tester (VR)", "empresa": "Magic Media", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/magic-media/j/2DA612A790/", "descripcion": "QA Game Tester VR Magic Media", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester - Age of Empires Legacy", "empresa": "Forgotten Empires", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/forgotten-empires/j/CD1CBD57C0/", "descripcion": "QA Tester Age of Empires", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Entry-Level QA Tester (Remote)", "empresa": "Ace IT Careers", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/ace-it-careers-1/j/82DEC766E6", "descripcion": "Entry Level QA Tester", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Functionality QA Video Games Tester", "empresa": "Universally Speaking", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/universally-speaking/j/0FF54DA9D1/", "descripcion": "Functionality QA Tester", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester", "empresa": "Lighthouse Games", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/lighthousegames/j/24444B8937", "descripcion": "QA Tester Lighthouse Games", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Senior Game Tester - QA", "empresa": "Side", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/sideinc/j/FA23F824C7/", "descripcion": "Senior Game Tester Side", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "English LQA Game Tester (Freelance)", "empresa": "PTW", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/ptw-i/j/BB20997271", "descripcion": "LQA Game Tester English PTW", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "LQA Game Tester English - Freelance", "empresa": "Side", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/sideinc/j/E1205DEFB3/", "descripcion": "LQA Game Tester English Side", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "LQA Game Tester Spanish - Freelance", "empresa": "Side", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/sideinc/j/C40356DAB7", "descripcion": "LQA Game Tester Spanish Side", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Entry-level Game QA Tester", "empresa": "PTW", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/ptw-i/j/01849E1031", "descripcion": "Entry Level QA Tester PTW", "fuente": "Workable", "fecha": "Febrero 2026"},
    {"titulo": "Russian Speaking Game Tester (Remote)", "empresa": "Keywords Studios", "ubicacion": "Remote", "salario": "", "url": "https://apply.workable.com/keywords-intl1/j/8ADED68C09", "descripcion": "Game Tester Russian Keywords", "fuente": "Workable", "fecha": "Febrero 2026"},
    # Ashby QA
    {"titulo": "QA Tester", "empresa": "Voldex Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/voldex/768a2eda-5ca3-4e99-843b-c959f10fb503", "descripcion": "QA Tester Voldex Games", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Game QA Tester", "empresa": "Windranger Labs", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/windranger/2d9787bf-2742-47ed-8a79-c9ee9dfd42cb", "descripcion": "Game QA Tester Windranger", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "QA Analyst (Gaming)", "empresa": "TapBlaze", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/tapblaze/51d4df32-7ac9-458b-9888-d2a57b0fe27e", "descripcion": "QA Analyst Gaming TapBlaze", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester (P2)", "empresa": "Voldex Games", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/Voldex/683feacf-796e-458a-9107-e1482601ebe2", "descripcion": "QA Tester P2 Voldex", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester - Paper.io 2", "empresa": "Voodoo", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/voodoo/8f2e636c-3bd6-4206-bef4-41541f5e764d", "descripcion": "QA Tester Paper.io Voodoo", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "QA Tester", "empresa": "Colonist", "ubicacion": "Remote Global", "salario": "", "url": "https://jobs.ashbyhq.com/colonist/4331e7c6-dbd7-479e-b170-a122b4064cf7", "descripcion": "QA Tester Colonist remote async", "fuente": "Ashby", "fecha": "Febrero 2026"},
    {"titulo": "Senior QA Automation Engineer", "empresa": "Playson", "ubicacion": "Remote", "salario": "", "url": "https://jobs.ashbyhq.com/playson/3e0bbc53-2d89-4053-94c3-30d08098c7e5", "descripcion": "Sr QA Automation Engineer Playson", "fuente": "Ashby", "fecha": "Febrero 2026"},
]

# Palabras clave para buscar trabajos
KEYWORDS = [
    "Unreal Engine developer",
    "Game Developer Unreal",
    "UE5 developer",
    "UE4 developer",
    "Gameplay Programmer",
    "Blueprint developer",
    "Technical Artist Unreal",
    "Environment Artist Unreal",
    "Level Designer Unreal",
    "Game Programmer C++",
    "Unreal Engine remote",
    "desarrollador Unreal Engine",
    "desarrollador videojuegos",
    "Game Tester",
    "QA Tester games",
    "Quality Assurance game",
    "Game Testing remote",
    "QA Analyst games",
    "Playtester",
    "Bug Tester games",
    "Python developer remote",
    "HTML developer remote",
]

# Ubicaciones aceptadas
UBICACIONES = ["remote", "remoto", "chile", "latam", "latin america",
               "south america", "worldwide", "anywhere", "global", "santiago"]

# Email para notificaciones
GMAIL_USER = os.environ.get("GMAIL_REMITENTE", "your@gmail.com")
GMAIL_APP_PASSWORD = ""  # <-- PEGA AQUÍ TU CONTRASEÑA DE APLICACIÓN

# Directorio de trabajo
WORK_DIR = os.path.dirname(os.path.abspath(__file__))

# URLs ya aplicadas exitosamente (no volver a postular)
URLS_YA_APLICADAS = [
    # Run 1
    "careers.gamebreaking.com",                                   # Gamebreaking Studios - EXITOSA
    # Run 3
    "thatsnomoonentertainment/jobs/5735137004",                   # That's No Moon - EXITOSA
    "unknownworlds/jobs/8297598002",                              # Unknown Worlds Subnautica 2 - EXITOSA
    "blackbirdinteractive/3185f339",                              # BBI Platforms (form filled)
    "blackbirdinteractive/5d242f27",                              # BBI Rendering (form filled)
    "blackbirdinteractive/6f33d670",                              # BBI Online (form filled)
    "triiodidestudios.applytojob.com",                            # Triiodide (form filled)
    # Run 4
    "oliver/jobs/7451407",                                        # OLIVER Agency - EXITOSA
    "hangar13/jobs/7526256003",                                   # Hangar 13 (2K) - EXITOSA
    "lever.co/zuru/a2b16d6f",                                    # ZURU (form filled)
    "lever.co/xsolla/88600493",                                  # Xsolla (form filled)
    "lever.co/gravisrobotics/ea0246d5",                           # Gravis Robotics (form filled)
    "ashbyhq.com/01c/6ee38004",                                  # Zero One Creative (email+CV)
    # Run 5
    "nightdivestudios/jobs/5099598008",                           # Nightdive Character Artist - EXITOSA
    "gamebreaking.com/p/0a9f219c3eeb",                           # Gamebreaking Studios (re-apply) - EXITOSA
    "unknownworlds/jobs/8297598002",                              # Unknown Worlds (re-apply) - ya estaba
]

# ============================================================
# CARTA DE PRESENTACIÓN ADAPTABLE
# ============================================================
def generar_carta_presentacion(empresa, puesto, descripcion=""):
    """Genera una carta de presentación adaptada a cada oferta"""

    # Detectar si el puesto es más técnico, artístico o de diseño
    puesto_lower = puesto.lower()
    desc_lower = descripcion.lower() if descripcion else ""
    es_python_web = any(k in puesto_lower or k in desc_lower for k in ["python", "html", "frontend", "web developer", "django", "flask", "full stack", "fullstack", "desarrollador web", "backend python"])
    es_tecnico = any(k in puesto_lower for k in ["programmer", "developer", "engineer", "c++", "programador"])
    es_artista = any(k in puesto_lower for k in ["artist", "art", "environment", "artista"])
    es_disenador = any(k in puesto_lower for k in ["designer", "design", "diseñador", "diseño"])

    # Seleccionar enfoque según el tipo de puesto
    if es_python_web:
        enfoque = (
            "Cuento con conocimientos medio-avanzados en Python y HTML/CSS, complementados con "
            "más de 9 años de experiencia en desarrollo de software con Unreal Engine (C++ y Blueprints). "
            "He desarrollado herramientas, scripts de automatización y pipelines de datos usando Python, "
            "así como interfaces web con HTML/CSS. Mi experiencia en desarrollo de software abarca tanto "
            "el frontend como el backend, con una sólida base en programación orientada a objetos, "
            "control de versiones (Git) y trabajo colaborativo remoto con equipos internacionales."
        )
    elif es_artista:
        enfoque = (
            "Mi especialización en creación de entornos 3D inmersivos y simulación en tiempo real "
            "me ha permitido desarrollar un ojo artístico técnico único. He contribuido al desarrollo "
            "de plugins reconocidos a nivel mundial en el ecosistema de Unreal Engine, dominando la "
            "creación de materiales, shaders y efectos visuales de alta fidelidad."
        )
    elif es_disenador:
        enfoque = (
            "Mi experiencia de más de 9 años diseñando niveles y entornos interactivos en "
            "Unreal Engine me ha dado una comprensión profunda del diseño de espacios jugables. "
            "He trabajado extensamente con World Partition, Blueprint scripting y sistemas "
            "procedurales para crear experiencias inmersivas."
        )
    else:
        enfoque = (
            "Mi profundo conocimiento de Unreal Engine 4 y 5, tanto en Blueprints como en C++, "
            "me permite abordar desafíos técnicos complejos. He contribuido al desarrollo de "
            "herramientas y plugins reconocidos dentro de la comunidad de Unreal Engine, trabajando "
            "con sistemas de simulación en tiempo real, renderizado, shaders y optimización de rendimiento."
        )

    # Detectar idioma preferido
    en_ingles = any(k in puesto.lower() for k in ["senior", "developer", "engineer", "artist", "designer", "lead"])

    if en_ingles and es_python_web:
        carta = f"""Dear Hiring Team at {empresa},

I am writing to express my strong interest in the {puesto} position. I am a software developer with intermediate-advanced proficiency in Python and HTML/CSS, complemented by over 9 years of professional experience in software development using C++ and visual scripting frameworks.

Throughout my career, I have developed automation tools, data processing scripts, and web interfaces using Python and HTML/CSS. I have strong experience with Git version control, object-oriented programming, API integration, and collaborative remote development with international teams. My background in real-time applications and performance-critical software gives me a solid foundation for building efficient, well-structured code.

My technical skills include Python (scripting, automation, data processing), HTML/CSS (responsive layouts, web interfaces), C++ programming, Git/version control, and experience working in agile, distributed teams. I am a self-driven developer with a proven ability to deliver high-quality results in remote environments.

I am confident that my experience and dedication would make me a valuable addition to your team. I would welcome the opportunity to discuss how I can contribute to {empresa}'s projects.

Best regards,
{DATOS_PERSONALES["nombre_completo"]}
Software Developer
Email: {DATOS_PERSONALES["email"]}
Phone: {DATOS_PERSONALES["telefono"]}"""
    elif en_ingles:
        carta = f"""Dear Hiring Team at {empresa},

I am writing to express my strong interest in the {puesto} position. With over 9 years of hands-on experience with Unreal Engine 4 and 5, I bring a deep technical foundation and proven track record in game development.

Throughout my career, I have been a key contributor to internationally recognized Unreal Engine projects and plugins used by thousands of developers worldwide. Since 2016, I have participated in every major version of these tools, building deep expertise in real-time simulation, shader development, material systems, rendering optimization, and collaborative remote development with international teams.

My technical skills include advanced Blueprint scripting, C++ programming, Python, HTML/CSS, Nanite, Lumen, Niagara VFX systems, level design, and performance profiling. I am a self-driven developer with a proven ability to deliver high-quality results in distributed, remote environments.

I am confident that my experience and dedication would make me a valuable addition to your team. I would welcome the opportunity to discuss how I can contribute to {empresa}'s projects.

Best regards,
{DATOS_PERSONALES["nombre_completo"]}
{DATOS_PERSONALES["titulo"]}
Email: {DATOS_PERSONALES["email"]}
Phone: {DATOS_PERSONALES["telefono"]}"""
    elif es_python_web:
        carta = f"""Estimado equipo de {empresa},

Me dirijo a ustedes para expresar mi interés en la posición de {puesto}. Soy desarrollador de software con conocimientos medio-avanzados en Python y HTML/CSS, complementados con más de 9 años de experiencia profesional en desarrollo de software.

{enfoque}

He desarrollado herramientas de automatización, scripts de procesamiento de datos e interfaces web. Mi experiencia incluye trabajo remoto con equipos internacionales, control de versiones con Git, programación orientada a objetos y metodologías ágiles de desarrollo colaborativo.

Mis competencias técnicas incluyen: Python (scripting, automatización, procesamiento de datos), HTML/CSS (layouts responsivos, interfaces web), C++, Git/control de versiones, y experiencia en equipos distribuidos y remotos.

Estoy convencido de que mi experiencia y dedicación serían un aporte valioso para su equipo. Quedo a disposición para conversar sobre cómo puedo contribuir a los proyectos de {empresa}.

Atentamente,
{DATOS_PERSONALES["nombre_completo"]}
Desarrollador de Software
Email: {DATOS_PERSONALES["email"]}
Teléfono: {DATOS_PERSONALES["telefono"]}"""
    else:
        carta = f"""Estimado equipo de {empresa},

Me dirijo a ustedes para expresar mi interés en la posición de {puesto}. Cuento con más de 9 años de experiencia trabajando con Unreal Engine 4 y 5, con un enfoque especializado en desarrollo de videojuegos y simulación en tiempo real.

{enfoque}

He participado como colaborador clave en el desarrollo de herramientas y plugins reconocidos internacionalmente dentro del ecosistema de Unreal Engine, utilizados por miles de desarrolladores en todo el mundo. Esta experiencia me ha permitido trabajar de forma remota con equipos internacionales, utilizando control de versiones y metodologías de desarrollo colaborativo a gran escala.

Mis competencias técnicas incluyen: Blueprints avanzado, C++, Python, HTML/CSS, Nanite, Lumen, Niagara VFX, diseño de niveles, materiales y shaders, y optimización de rendimiento.

Estoy convencido de que mi experiencia y dedicación serían un aporte valioso para su equipo. Quedo a disposición para conversar sobre cómo puedo contribuir a los proyectos de {empresa}.

Atentamente,
{DATOS_PERSONALES["nombre_completo"]}
{DATOS_PERSONALES["titulo"]}
Email: {DATOS_PERSONALES["email"]}
Teléfono: {DATOS_PERSONALES["telefono"]}"""

    return carta


# ============================================================
# BUSCADOR DE OFERTAS - Usa el mismo buscador que ya funciona
# ============================================================
class BuscadorOfertas:
    """Busca ofertas importando resultados del buscador_trabajos.py"""

    def __init__(self):
        self.ofertas = []

    def buscar_todas(self):
        """Ejecuta búsqueda usando el buscador_trabajos.py que ya funciona"""
        logging.info("=" * 60)
        logging.info("INICIANDO BÚSQUEDA DE OFERTAS (8 fuentes)")
        logging.info("=" * 60)

        try:
            # Importar el buscador que ya funciona
            import sys
            sys.path.insert(0, WORK_DIR)
            import buscador_trabajos as bt

            # Crear sesión HTTP
            sesion = bt.crear_sesion_http()

            # Buscar en TODAS las fuentes (las mismas 8 que funcionan)
            fuentes = [
                ("RemoteOK", bt.buscar_remoteok),
                ("Indeed RSS", bt.buscar_indeed_rss),
                ("LinkedIn", bt.buscar_linkedin_publico),
                ("GameJobs.co", bt.buscar_gamedevjobs),
                ("Hitmarker", bt.buscar_hitmarker),
                ("Working Nomads", bt.buscar_workingnomads),
                ("Remotive", bt.buscar_remotive),
                ("Jooble RSS", bt.buscar_jooble_rss),
            ]

            todas = []
            for nombre, funcion in fuentes:
                try:
                    logging.info(f"Buscando en {nombre}...")
                    resultados = funcion(sesion)
                    todas.extend(resultados)
                    logging.info(f"  -> {nombre}: {len(resultados)} ofertas")
                except Exception as e:
                    logging.warning(f"  -> Error en {nombre}: {e}")

            # Eliminar duplicados
            unicas = bt.eliminar_duplicados(todas)

            # Convertir formato OfertaTrabajo a diccionario para el auto-postulador
            for oferta in unicas:
                self.ofertas.append({
                    "titulo": oferta.titulo,
                    "empresa": oferta.empresa,
                    "ubicacion": oferta.ubicacion,
                    "salario": oferta.salario,
                    "url": oferta.enlace,
                    "descripcion": oferta.descripcion,
                    "fuente": oferta.fuente,
                    "fecha": oferta.fecha_publicacion,
                })

            logging.info(f"\nTotal ofertas únicas encontradas: {len(self.ofertas)}")

        except ImportError as e:
            logging.error(f"No se pudo importar buscador_trabajos.py: {e}")
            logging.info("Intentando búsqueda directa de respaldo...")
            self._busqueda_respaldo()

        return self.ofertas

    def _busqueda_respaldo(self):
        """Búsqueda directa si no se puede importar el buscador principal"""
        import feedparser

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        keywords = ["unreal", "ue5", "ue4", "game dev", "gameplay", "videojuego",
                     "blueprint", "level design", "environment artist", "technical artist",
                     "game design", "c++ game", "ocean", "game prog"]

        def es_relevante(texto):
            return any(kw in texto.lower() for kw in keywords)

        # RemoteOK
        try:
            resp = session.get("https://remoteok.com/api", timeout=20)
            if resp.status_code == 200:
                for item in resp.json()[1:]:
                    titulo = item.get("position", "")
                    tags = " ".join(item.get("tags", []))
                    if es_relevante(f"{titulo} {tags} {item.get('description', '')}"):
                        self.ofertas.append({
                            "titulo": titulo,
                            "empresa": item.get("company", ""),
                            "ubicacion": item.get("location", "Remote"),
                            "salario": item.get("salary", "No especificado"),
                            "url": item.get("url", ""),
                            "descripcion": item.get("description", "")[:500],
                            "fuente": "RemoteOK",
                            "fecha": item.get("date", ""),
                        })
        except Exception as e:
            logging.warning(f"Error RemoteOK: {e}")

        # Remotive
        try:
            resp = session.get("https://remotive.com/api/remote-jobs?category=software-dev&limit=100", timeout=20)
            if resp.status_code == 200:
                for job in resp.json().get("jobs", []):
                    titulo = job.get("title", "")
                    if es_relevante(f"{titulo} {job.get('description', '')}"):
                        self.ofertas.append({
                            "titulo": titulo,
                            "empresa": job.get("company_name", ""),
                            "ubicacion": job.get("candidate_required_location", "Remote"),
                            "salario": job.get("salary", "No especificado"),
                            "url": job.get("url", ""),
                            "descripcion": job.get("description", "")[:500],
                            "fuente": "Remotive",
                            "fecha": job.get("publication_date", ""),
                        })
        except Exception as e:
            logging.warning(f"Error Remotive: {e}")

        # Indeed RSS
        for query in ["unreal+engine+developer+remote", "game+developer+remote",
                       "unreal+engine+chile", "game+developer+chile",
                       "ue5+developer+remote", "technical+artist+unreal+remote",
                       "game+tester+remote", "qa+tester+games+remote",
                       "game+testing+remote", "playtester+remote",
                       "python+developer+remote", "html+developer+remote"]:
            try:
                url = f"https://www.indeed.com/rss?q={query}&sort=date&fromage=30"
                resp = session.get(url, timeout=20)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.content)
                    for entry in feed.entries:
                        titulo = entry.get("title", "")
                        if es_relevante(f"{titulo} {entry.get('summary', '')}"):
                            self.ofertas.append({
                                "titulo": titulo,
                                "empresa": entry.get("author", ""),
                                "ubicacion": "Ver oferta",
                                "salario": "No especificado",
                                "url": entry.get("link", ""),
                                "descripcion": entry.get("summary", "")[:500],
                                "fuente": "Indeed",
                                "fecha": entry.get("published", ""),
                            })
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Error Indeed ({query}): {e}")

        # Working Nomads
        try:
            resp = session.get("https://www.workingnomads.com/api/exposed_jobs/", timeout=20)
            if resp.status_code == 200:
                for item in resp.json():
                    titulo = item.get("title", "")
                    if es_relevante(f"{titulo} {item.get('description', '')}"):
                        self.ofertas.append({
                            "titulo": titulo,
                            "empresa": item.get("company_name", ""),
                            "ubicacion": item.get("location", "Remote"),
                            "salario": "No especificado",
                            "url": item.get("url", ""),
                            "descripcion": item.get("description", "")[:500],
                            "fuente": "Working Nomads",
                            "fecha": item.get("pub_date", ""),
                        })
        except Exception as e:
            logging.warning(f"Error Working Nomads: {e}")

        # Eliminar duplicados
        vistos = set()
        unicas = []
        for oferta in self.ofertas:
            clave = hashlib.md5(
                f"{oferta['titulo'].lower()}{oferta['empresa'].lower()}".encode()
            ).hexdigest()
            if clave not in vistos:
                vistos.add(clave)
                unicas.append(oferta)
        self.ofertas = unicas
        logging.info(f"Búsqueda de respaldo: {len(self.ofertas)} ofertas únicas")


# ============================================================
# AUTO-POSTULADOR CON SELENIUM
# ============================================================
class AutoPostulador:
    """Automatiza el proceso de postulación usando el navegador"""

    def __init__(self, headless=False, usar_perfil=True):
        """
        headless=False para que puedas VER lo que hace el navegador.
        usar_perfil=True para usar el perfil de Edge con sesión de Google.
        """
        self.options = Options()
        self.options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

        if headless:
            self.options.add_argument("--headless")

        # Usar perfil de Edge existente (con sesión de Google iniciada)
        if usar_perfil:
            edge_user_data = r"C:\Users\eos\AppData\Local\Microsoft\Edge\User Data"
            self.options.add_argument(f"--user-data-dir={edge_user_data}")
            self.options.add_argument("--profile-directory=Default")

        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--start-maximized")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])

        self.driver = None
        self.postulaciones_exitosas = []
        self.postulaciones_fallidas = []

    def iniciar_navegador(self):
        """Abre el navegador Edge"""
        logging.info("Iniciando navegador Edge (con perfil de usuario)...")
        self.driver = webdriver.Edge(options=self.options)
        self.driver.implicitly_wait(2)
        logging.info("Navegador listo (sesión de Google disponible).")

    def cerrar_navegador(self):
        """Cierra el navegador"""
        if self.driver:
            self.driver.quit()
            logging.info("Navegador cerrado.")

    def postular_a_oferta(self, oferta):
        """Intenta postular automáticamente a una oferta"""
        url = oferta.get("url", "")
        empresa = oferta.get("empresa", "")
        puesto = oferta.get("titulo", "")

        if not url:
            logging.warning(f"Sin URL para: {puesto} en {empresa}")
            return False

        logging.info(f"\n{'='*50}")
        logging.info(f"POSTULANDO: {puesto} en {empresa}")
        logging.info(f"URL: {url}")
        logging.info(f"{'='*50}")

        try:
            # Generar carta de presentación
            carta = generar_carta_presentacion(empresa, puesto, oferta.get("descripcion", ""))

            # Detectar plataforma y usar handler específico
            aplicado = False
            if "greenhouse.io" in url or "epicgames.com/careers" in url:
                aplicado = self._postular_greenhouse(url, carta)
            elif "lever.co" in url:
                aplicado = self._postular_lever(url, carta)
            elif "bamboohr.com" in url:
                aplicado = self._postular_bamboohr(url, carta)
            elif "ashbyhq.com" in url or "ashby.com" in url:
                aplicado = self._postular_ashby(url, carta)
            elif "workable.com" in url:
                aplicado = self._postular_workable(url, carta)
            elif "smartrecruiters.com" in url:
                aplicado = self._postular_smartrecruiters(url, carta)
            elif "applytojob.com" in url:
                aplicado = self._postular_generic_ats(url, carta)
            elif "linkedin.com" in url:
                aplicado = self._postular_linkedin(url, carta)
            elif "globant.com" in url or "getonbrd.com" in url:
                aplicado = self._postular_con_login(url, carta)
            else:
                # Handler genérico para otros sitios
                self.driver.get(url)
                time.sleep(4)
                aplicado = self._intentar_aplicar_directo(carta)

            if aplicado:
                self.postulaciones_exitosas.append(oferta)
                logging.info(f"POSTULACIÓN EXITOSA: {puesto} en {empresa}")
                return True
            else:
                self._guardar_postulacion_pendiente(oferta, carta)
                self.postulaciones_fallidas.append(oferta)
                logging.info(f"POSTULACIÓN GUARDADA COMO PENDIENTE: {puesto} en {empresa}")
                return False

        except Exception as e:
            error_msg = str(e)
            # Re-lanzar errores de sesión para que el loop principal reinicie el navegador
            if "invalid session id" in error_msg or "session deleted" in error_msg or "not connected to DevTools" in error_msg:
                raise
            logging.error(f"Error postulando a {puesto}: {e}")
            carta = generar_carta_presentacion(empresa, puesto, oferta.get("descripcion", ""))
            self._guardar_postulacion_pendiente(oferta, carta)
            self.postulaciones_fallidas.append(oferta)
            return False

    def _manejar_nueva_ventana(self):
        """Si se abrió una nueva pestaña/ventana, cambiar a ella"""
        handles = self.driver.window_handles
        if len(handles) > 1:
            self.driver.switch_to.window(handles[-1])
            time.sleep(2)
            return True
        return False

    def _cerrar_ventanas_extra(self):
        """Cerrar pestañas extra y volver a la principal"""
        handles = self.driver.window_handles
        while len(handles) > 1:
            self.driver.switch_to.window(handles[-1])
            self.driver.close()
            handles = self.driver.window_handles
        if handles:
            self.driver.switch_to.window(handles[0])

    def _esperar_y_llenar(self, selectores, valor, nombre_campo="campo"):
        """Intenta llenar un campo con múltiples selectores"""
        if not valor:
            return False
        for selector in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elementos:
                    if elem.is_displayed() and elem.is_enabled():
                        elem.clear()
                        elem.send_keys(valor)
                        logging.info(f"  Campo '{nombre_campo}' llenado: {valor[:30]}...")
                        return True
            except:
                continue
        return False

    def _find_first_match(self, selectors):
        """Encuentra el primer elemento visible que coincida con alguno de los selectores CSS.
        Acepta una lista de selectores individuales o un string con selectores separados por coma."""
        if isinstance(selectors, str):
            selectors = [s.strip() for s in selectors.split(",")]
        for selector in selectors:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elementos:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            return elem
                    except:
                        continue
            except:
                continue
        return None

    def _esperar_renderizado_spa(self, timeout=12):
        """Espera inteligente para SPAs. Verifica que spinners desaparecieron,
        inputs se estabilizaron y contenido cargó. Reemplaza time.sleep fijos."""
        import time as _time
        start = _time.time()
        prev_input_count = 0
        stable_cycles = 0

        while _time.time() - start < timeout:
            try:
                # Verificar si hay spinners/loaders activos
                spinners = self.driver.find_elements(By.CSS_SELECTOR,
                    "[class*='spinner'], [class*='loading'], [class*='loader'], "
                    "[class*='Spinner'], [class*='Loading'], [role='progressbar']")
                spinner_visible = any(s.is_displayed() for s in spinners if s)

                if spinner_visible:
                    stable_cycles = 0
                    _time.sleep(0.5)
                    continue

                # Contar inputs visibles y verificar estabilidad
                inputs = self.driver.find_elements(By.CSS_SELECTOR,
                    "input, textarea, select")
                current_count = len(inputs)

                # Verificar que hay contenido
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                if len(body_text.strip()) < 50:
                    stable_cycles = 0
                    _time.sleep(0.5)
                    continue

                if current_count == prev_input_count and current_count > 0:
                    stable_cycles += 1
                else:
                    stable_cycles = 0
                    prev_input_count = current_count

                # Si llevamos 3 ciclos estables (1.5s), estamos listos
                if stable_cycles >= 3:
                    logging.info(f"  SPA renderizada ({_time.time()-start:.1f}s, {current_count} campos)")
                    return True

                _time.sleep(0.5)
            except:
                _time.sleep(0.5)

        logging.info(f"  SPA timeout ({timeout}s)")
        return False

    def _verificar_submit(self, url_antes=None):
        """Verificación post-submit universal. Chequea si el envío fue exitoso.
        Retorna True (éxito confirmado), False (error detectado), None (indeterminado)."""
        try:
            time.sleep(2)
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            url_actual = self.driver.current_url.lower()

            # 1. Texto de confirmación
            confirmaciones = [
                "thank you", "thanks for applying", "application received",
                "application submitted", "successfully submitted",
                "we have received", "you have applied", "application complete",
                "gracias por postular", "postulación enviada", "solicitud recibida",
                "your application has been", "we'll be in touch",
                "application has been submitted", "thank you for your interest",
                "thanks for your application", "submitted successfully",
                "you're all set", "we got your application",
            ]
            for conf in confirmaciones:
                if conf in page_text:
                    logging.info(f"  Submit CONFIRMADO: '{conf}' encontrado")
                    return True

            # 2. URL cambió a página de confirmación
            if url_antes:
                url_antes_lower = url_antes.lower()
                if url_actual != url_antes_lower:
                    if any(kw in url_actual for kw in ["thanks", "thank-you", "confirmation",
                                                         "success", "submitted", "complete"]):
                        logging.info(f"  Submit CONFIRMADO: URL cambió a {url_actual}")
                        return True

            # 3. Errores visibles
            errores = self.driver.find_elements(By.CSS_SELECTOR,
                "[class*='error'], [class*='Error'], [role='alert'], "
                "[class*='invalid'], [class*='Invalid'], .field-error, "
                ".form-error, [class*='required-error']")
            errores_visibles = []
            for err in errores:
                try:
                    if err.is_displayed() and err.text.strip():
                        errores_visibles.append(err.text.strip()[:100])
                except:
                    continue
            if errores_visibles:
                logging.warning(f"  Submit ERROR detectado: {errores_visibles[:3]}")
                return False

            # 4. Formulario desapareció (inputs ya no visibles)
            inputs_visibles = self.driver.find_elements(By.CSS_SELECTOR,
                "input[type='text']:not([type='hidden']), input[type='email'], textarea")
            inputs_activos = sum(1 for i in inputs_visibles if i.is_displayed())
            if inputs_activos == 0:
                logging.info("  Submit probablemente exitoso: formulario desapareció")
                return True

            logging.info("  Submit resultado indeterminado")
            return None
        except Exception as e:
            logging.debug(f"  Error verificando submit: {e}")
            return None

    def _detectar_idioma_pagina(self):
        """Detecta si la página actual está en inglés o español"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            # Palabras clave en español
            es_espanol = sum(1 for w in ["postular", "requisitos", "experiencia", "ubicación",
                                          "empresa", "descripción", "habilidades", "enviar",
                                          "nombre", "apellido", "teléfono"]
                            if w in page_text)
            return "es" if es_espanol >= 3 else "en"
        except:
            return "en"

    def _detectar_idioma(self, page_text):
        """Detecta idioma basándose en texto proporcionado. Retorna 'EN' o 'ES'."""
        text_lower = page_text.lower() if isinstance(page_text, str) else ""
        es_espanol = sum(1 for w in ["postular", "requisitos", "experiencia", "ubicación",
                                      "empresa", "descripción", "habilidades", "enviar",
                                      "nombre", "apellido", "teléfono"]
                        if w in text_lower)
        return "ES" if es_espanol >= 3 else "EN"

    def _subir_cv(self, idioma="en"):
        """Sube el CV al primer input de archivo disponible (EN o ES según idioma)"""
        if idioma == "es":
            cv_path = DATOS_PERSONALES["cv_path"]
        else:
            cv_path = DATOS_PERSONALES.get("cv_path_en", DATOS_PERSONALES["cv_path"])

        if not os.path.exists(cv_path):
            logging.warning(f"  CV no encontrado: {cv_path}")
            # Fallback al otro idioma
            cv_path = DATOS_PERSONALES["cv_path"]
            if not os.path.exists(cv_path):
                return False

        file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        for fi in file_inputs:
            try:
                fi.send_keys(cv_path)
                logging.info(f"  CV subido ({idioma.upper()}): {os.path.basename(cv_path)}")
                time.sleep(2)
                return True
            except:
                continue
        return False

    def _escribir_carta(self, carta):
        """Escribe la carta de presentación en textareas disponibles"""
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        for ta in textareas:
            try:
                if ta.is_displayed() and ta.is_enabled():
                    name = (ta.get_attribute("name") or "").lower()
                    placeholder = (ta.get_attribute("placeholder") or "").lower()
                    aria = (ta.get_attribute("aria-label") or "").lower()
                    label_text = f"{name} {placeholder} {aria}"

                    if any(kw in label_text for kw in
                           ["cover", "letter", "message", "carta", "presentacion",
                            "about", "why", "additional", "nota", "comentario",
                            "introduction", "yourself", "summary"]):
                        ta.clear()
                        ta.send_keys(carta)
                        logging.info("  Carta de presentación escrita.")
                        return True
            except:
                continue

        # Si no encontró campo específico, intentar con el primer textarea largo vacío
        for ta in textareas:
            try:
                if ta.is_displayed() and ta.is_enabled() and not ta.get_attribute("value"):
                    ta.send_keys(carta)
                    logging.info("  Carta escrita en textarea disponible.")
                    return True
            except:
                continue
        return False

    def _hacer_submit(self):
        """Busca y hace clic en el botón de envío con verificación post-submit"""
        botones_submit = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'send')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'enviar')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'postular')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'soumettre')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'envoyer')]",
            "//a[contains(@class, 'submit')]",
        ]

        url_antes = self.driver.current_url

        for xpath in botones_submit:
            try:
                botones = self.driver.find_elements(By.XPATH, xpath)
                for btn in botones:
                    if btn.is_displayed() and btn.is_enabled():
                        logging.info("  Enviando formulario...")
                        btn.click()
                        time.sleep(4)
                        # Verificar si el submit fue exitoso
                        resultado = self._verificar_submit(url_antes)
                        if resultado is False:
                            logging.warning("  Submit falló - errores detectados en formulario")
                            return False
                        elif resultado is True:
                            logging.info("  Formulario enviado y VERIFICADO!")
                            return True
                        else:
                            # Indeterminado - asumir éxito como antes
                            logging.info("  Formulario enviado (sin confirmación explícita)")
                            return True
            except:
                continue
        return False

    def _analizar_y_llenar_pagina(self, carta):
        """Analiza TODA la página visible, identifica cada campo y lo rellena inteligentemente.
        Primero escanea, luego rellena. Más adaptativo que selectores fijos."""
        logging.info("  [Análisis inteligente de página]")
        # Esperar a que la SPA renderice completamente
        self._esperar_renderizado_spa(timeout=8)

        # PASO 1: Escanear todos los campos visibles del formulario
        campos_encontrados = []
        try:
            # Buscar todos los inputs visibles
            inputs = self.driver.find_elements(By.CSS_SELECTOR,
                "input[type='text'], input[type='email'], input[type='tel'], "
                "input[type='url'], input[type='number'], input:not([type])")
            for inp in inputs:
                try:
                    if not inp.is_displayed() or not inp.is_enabled():
                        continue
                    info = {
                        "element": inp,
                        "type": inp.get_attribute("type") or "text",
                        "name": (inp.get_attribute("name") or "").lower(),
                        "id": (inp.get_attribute("id") or "").lower(),
                        "placeholder": (inp.get_attribute("placeholder") or "").lower(),
                        "autocomplete": (inp.get_attribute("autocomplete") or "").lower(),
                        "aria_label": (inp.get_attribute("aria-label") or "").lower(),
                        "label_text": "",
                        "value": inp.get_attribute("value") or "",
                    }
                    # Buscar label asociada
                    try:
                        inp_id = inp.get_attribute("id")
                        if inp_id:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{inp_id}']")
                            info["label_text"] = label.text.lower()
                    except:
                        pass
                    # Buscar texto del parent container
                    if not info["label_text"]:
                        try:
                            parent = inp.find_element(By.XPATH, "./..")
                            parent_text = parent.text.lower()[:200]
                            info["label_text"] = parent_text
                        except:
                            pass
                    campos_encontrados.append(info)
                except:
                    continue

            # Buscar textareas
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for ta in textareas:
                try:
                    if ta.is_displayed() and ta.is_enabled():
                        campos_encontrados.append({
                            "element": ta,
                            "type": "textarea",
                            "name": (ta.get_attribute("name") or "").lower(),
                            "id": (ta.get_attribute("id") or "").lower(),
                            "placeholder": (ta.get_attribute("placeholder") or "").lower(),
                            "autocomplete": "",
                            "aria_label": (ta.get_attribute("aria-label") or "").lower(),
                            "label_text": "",
                            "value": ta.get_attribute("value") or ta.text or "",
                        })
                except:
                    continue

            # Buscar selects
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel in selects:
                try:
                    if sel.is_displayed():
                        campos_encontrados.append({
                            "element": sel,
                            "type": "select",
                            "name": (sel.get_attribute("name") or "").lower(),
                            "id": (sel.get_attribute("id") or "").lower(),
                            "placeholder": "",
                            "autocomplete": "",
                            "aria_label": (sel.get_attribute("aria-label") or "").lower(),
                            "label_text": "",
                            "value": "",
                        })
                except:
                    continue

            # File inputs (ocultos incluidos)
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

        except Exception as e:
            logging.info(f"  Error escaneando página: {e}")
            campos_encontrados = []
            file_inputs = []

        logging.info(f"  Campos encontrados: {len(campos_encontrados)} inputs/textareas/selects, {len(file_inputs)} file inputs")

        # PASO 2: Clasificar y rellenar cada campo
        idioma = self._detectar_idioma_pagina()
        en_ingles = idioma == "en"
        campos_llenados = 0

        for campo in campos_encontrados:
            elem = campo["element"]
            context = f"{campo['name']} {campo['id']} {campo['placeholder']} {campo['autocomplete']} {campo['aria_label']} {campo['label_text']}"

            # Si ya tiene valor, saltar (a menos que sea placeholder)
            if campo["value"] and campo["type"] != "textarea" and len(campo["value"]) > 2:
                continue

            try:
                valor = None

                # --- INPUTS DE TEXTO ---
                if campo["type"] in ("text", "email", "tel", "url", "number", ""):
                    # Email
                    if any(kw in context for kw in ["email", "correo", "e-mail"]):
                        valor = DATOS_PERSONALES["email"]
                    # Teléfono
                    elif any(kw in context for kw in ["phone", "tel", "móvil", "celular", "teléfono"]):
                        valor = DATOS_PERSONALES["telefono"]
                    # Nombre completo
                    elif any(kw in context for kw in ["full name", "full_name", "fullname", "nombre completo", "your name"]):
                        valor = DATOS_PERSONALES["nombre_completo"]
                    # Primer nombre
                    elif any(kw in context for kw in ["first name", "first_name", "firstname", "given-name", "nombre"]) and not any(kw in context for kw in ["last", "apellido", "company", "empresa"]):
                        valor = DATOS_PERSONALES["nombre"]
                    # Apellido
                    elif any(kw in context for kw in ["last name", "last_name", "lastname", "family-name", "surname", "apellido"]):
                        valor = DATOS_PERSONALES["apellido"]
                    # Ciudad/Ubicación
                    elif any(kw in context for kw in ["city", "location", "ciudad", "ubicación", "address"]) and not any(kw in context for kw in ["email", "web", "url"]):
                        valor = f"{DATOS_PERSONALES['ciudad']}, {DATOS_PERSONALES['pais']}"
                    # LinkedIn
                    elif any(kw in context for kw in ["linkedin"]):
                        valor = DATOS_PERSONALES.get("linkedin", "")
                    # Portfolio/Website
                    elif any(kw in context for kw in ["portfolio", "website", "artstation", "reel", "demo"]):
                        valor = DATOS_PERSONALES.get("portfolio", "")
                    # Organización/Empresa actual
                    elif any(kw in context for kw in ["company", "organization", "org", "current employer", "empresa"]):
                        valor = "Independent Game Developer"
                    # Desired start date
                    elif any(kw in context for kw in ["start date", "fecha de inicio", "when can you start", "disponibilidad"]):
                        valor = "Immediately / As soon as possible"
                    # Salary
                    elif any(kw in context for kw in ["salary", "compensation", "salario", "expectativa salarial"]):
                        valor = "Negotiable / Open to discussion"
                    # How did you hear
                    elif any(kw in context for kw in ["how did you hear", "how did you find", "referral source", "cómo te enteraste", "cómo nos encontraste"]):
                        valor = "Online job search"
                    # Nombre genérico (si autocomplete=name o name=name)
                    elif campo["autocomplete"] == "name" or campo["name"] == "name":
                        valor = DATOS_PERSONALES["nombre_completo"]

                    if valor:
                        elem.click()
                        time.sleep(0.2)
                        elem.clear()
                        elem.send_keys(valor)
                        campos_llenados += 1
                        logging.info(f"  Llenado: '{context[:50]}' -> '{valor[:30]}'")

                # --- TEXTAREAS ---
                elif campo["type"] == "textarea":
                    if any(kw in context for kw in ["cover", "letter", "carta", "presentación", "why", "about yourself",
                                                     "introduction", "message", "additional", "summary"]):
                        elem.click()
                        elem.clear()
                        elem.send_keys(carta[:3000])
                        campos_llenados += 1
                        logging.info(f"  Carta escrita en textarea")
                    elif any(kw in context for kw in ["how did you hear", "referral", "cómo te enteraste"]):
                        elem.click()
                        elem.clear()
                        elem.send_keys("Online job search")
                        campos_llenados += 1

                # --- SELECTS ---
                elif campo["type"] == "select":
                    from selenium.webdriver.support.ui import Select
                    try:
                        select_obj = Select(elem)
                        options_text = [o.text.lower() for o in select_obj.options]
                        # Intentar seleccionar opciones inteligentes
                        if any("country" in context or "país" in context for _ in [1]):
                            for opt in select_obj.options:
                                if "chile" in opt.text.lower():
                                    select_obj.select_by_visible_text(opt.text)
                                    campos_llenados += 1
                                    logging.info(f"  Select country -> Chile")
                                    break
                        elif any(kw in context for kw in ["state", "province", "estado", "región"]):
                            for pref in ["n/a", "outside", "other", "not applicable"]:
                                for opt in select_obj.options:
                                    if pref in opt.text.lower():
                                        select_obj.select_by_visible_text(opt.text)
                                        campos_llenados += 1
                                        logging.info(f"  Select state -> {opt.text}")
                                        break
                                else:
                                    continue
                                break
                        elif any("yes" in o for o in options_text):
                            for opt in select_obj.options:
                                if "yes" in opt.text.lower():
                                    select_obj.select_by_visible_text(opt.text)
                                    campos_llenados += 1
                                    break
                    except:
                        pass

            except Exception as e:
                logging.debug(f"  Error rellenando campo: {e}")
                continue

        # PASO 3: Subir CV
        if file_inputs:
            cv_path = DATOS_PERSONALES["cv_path_en"] if en_ingles else DATOS_PERSONALES["cv_path"]
            if not os.path.exists(cv_path):
                cv_path = DATOS_PERSONALES["cv_path"]
            for fi in file_inputs:
                try:
                    fi.send_keys(cv_path)
                    logging.info(f"  CV subido ({idioma.upper()}): {os.path.basename(cv_path)}")
                    campos_llenados += 1
                    time.sleep(2)
                    break
                except:
                    continue

        logging.info(f"  Total campos rellenados: {campos_llenados}")
        return campos_llenados >= 1  # Necesita al menos 1 campo para considerar éxito

    def _llenar_campos_comunes(self, carta):
        """Llena todos los campos comunes del formulario"""
        llenado = False
        idioma = self._detectar_idioma_pagina()
        logging.info(f"  Idioma detectado: {idioma.upper()}")

        # Nombre
        if self._esperar_y_llenar([
            "input[name*='first_name' i]", "input[name*='firstName' i]",
            "input[id*='first_name' i]", "input[id*='firstName' i]",
            "input[placeholder*='First' i]", "input[aria-label*='First' i]",
            "input[name*='nombre' i]:not([name*='completo'])",
            "input[autocomplete='given-name']",
        ], DATOS_PERSONALES["nombre"], "nombre"):
            llenado = True

        # Apellido
        if self._esperar_y_llenar([
            "input[name*='last_name' i]", "input[name*='lastName' i]",
            "input[id*='last_name' i]", "input[id*='lastName' i]",
            "input[placeholder*='Last' i]", "input[aria-label*='Last' i]",
            "input[name*='apellido' i]",
            "input[autocomplete='family-name']",
        ], DATOS_PERSONALES["apellido"], "apellido"):
            llenado = True

        # Nombre completo (si no hay campos separados)
        if not llenado:
            if self._esperar_y_llenar([
                "input[name*='full_name' i]", "input[name*='fullName' i]",
                "input[name='name']", "input[id='name']",
                "input[placeholder*='Full name' i]", "input[placeholder*='Nombre completo' i]",
                "input[placeholder*='Your name' i]", "input[aria-label*='Full name' i]",
                "input[autocomplete='name']",
            ], DATOS_PERSONALES["nombre_completo"], "nombre_completo"):
                llenado = True

        # Email
        if self._esperar_y_llenar([
            "input[type='email']", "input[name*='email' i]",
            "input[id*='email' i]", "input[placeholder*='email' i]",
            "input[placeholder*='correo' i]", "input[autocomplete='email']",
        ], DATOS_PERSONALES["email"], "email"):
            llenado = True

        # Teléfono
        if self._esperar_y_llenar([
            "input[type='tel']", "input[name*='phone' i]",
            "input[name*='telefono' i]", "input[id*='phone' i]",
            "input[placeholder*='phone' i]", "input[placeholder*='teléfono' i]",
            "input[autocomplete='tel']",
        ], DATOS_PERSONALES["telefono"], "telefono"):
            llenado = True

        # Ciudad/Ubicación
        self._esperar_y_llenar([
            "input[name*='city' i]", "input[name*='ciudad' i]",
            "input[name*='location' i]", "input[placeholder*='City' i]",
            "input[placeholder*='Ciudad' i]", "input[placeholder*='Location' i]",
            "input[autocomplete='address-level2']",
        ], f"{DATOS_PERSONALES['ciudad']}, {DATOS_PERSONALES['pais']}", "ciudad")

        # LinkedIn
        if DATOS_PERSONALES.get("linkedin"):
            self._esperar_y_llenar([
                "input[name*='linkedin' i]", "input[id*='linkedin' i]",
                "input[placeholder*='LinkedIn' i]",
            ], DATOS_PERSONALES["linkedin"], "linkedin")

        # Portfolio/Website
        if DATOS_PERSONALES.get("portfolio"):
            self._esperar_y_llenar([
                "input[name*='portfolio' i]", "input[name*='website' i]",
                "input[name*='url' i]", "input[placeholder*='Portfolio' i]",
                "input[placeholder*='Website' i]",
            ], DATOS_PERSONALES["portfolio"], "portfolio")

        # Subir CV (en el idioma correcto)
        if self._subir_cv(idioma):
            llenado = True

        # Carta de presentación
        self._escribir_carta(carta)

        return llenado

    # ============================================================
    # HANDLERS ESPECÍFICOS POR PLATAFORMA
    # ============================================================
    def _cerrar_cookie_banners(self):
        """Cierra cookie banners y overlays que bloquean formularios"""
        try:
            cookie_selectors = [
                "button[id*='cookie']", "button[class*='cookie']",
                "a[id*='cookie']", "button[id*='accept']",
                "button[class*='accept']", "button[class*='consent']",
                "button[id*='consent']", "button[class*='dismiss']",
                "button[aria-label*='close']", "button[aria-label*='accept']",
                "button[aria-label*='dismiss']", ".cookie-banner button",
                "#onetrust-accept-btn-handler", ".cc-btn.cc-dismiss",
                "[data-testid='cookie-accept']", ".js-cookie-consent-agree",
                "button.accept-cookies", "#cookie-accept", "#accept-cookies",
                ".cookie-notice button", ".gdpr-banner button",
            ]
            for sel in cookie_selectors:
                try:
                    btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for btn in btns:
                        if btn.is_displayed():
                            btn.click()
                            logging.info(f"  Cookie banner cerrado: {sel}")
                            time.sleep(1)
                            return True
                except:
                    continue
            # Intentar via JS eliminar overlays fixed
            self.driver.execute_script("""
                document.querySelectorAll('[class*="cookie"], [class*="consent"], [id*="cookie"], [id*="consent"], [class*="gdpr"]').forEach(el => {
                    if (el.offsetHeight > 50 && (el.style.position === 'fixed' || window.getComputedStyle(el).position === 'fixed')) {
                        el.remove();
                    }
                });
            """)
        except Exception as e:
            logging.debug(f"  Cookie banner check: {e}")
        return False

    def _pagina_expirada(self, url_original=None):
        """Detecta rápidamente si la página es un error 404 o oferta cerrada.
        Si detecta expiración y url_original se proporciona, la guarda en urls_expiradas.txt"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            url_actual = self.driver.current_url.lower()
            titulo = self.driver.title.lower()

            indicadores_expirada = [
                "page not found", "404 not found", "404 error",
                "no longer available", "not found",
                "position has been filled", "job has been closed",
                "this position is no longer", "no longer accepting",
                "sorry, that page", "job not found", "position closed",
                "this job is no longer", "does not exist",
                "ya no está disponible", "posición cerrada",
                "no jobs found", "the job you are looking for",
                "this job has expired", "job expired",
                "no longer open", "position is closed",
                "couldn't find anything", "has been removed",
                "might have closed", "sorry, we couldn",
                "posting you're looking for",
            ]
            # Para páginas JS-renderizadas (Workable, etc), si hay muy poco texto
            # es porque aún no cargó - NO marcar como expirada
            if len(page_text.strip()) < 50:
                return False

            for ind in indicadores_expirada:
                if ind in page_text[:2000] or ind in titulo:
                    if url_original:
                        guardar_url_expirada(url_original)
                    return True

            # Si la URL redirigió a una página genérica de careers
            if url_actual.endswith("/careers") or url_actual.endswith("/jobs"):
                if url_original:
                    guardar_url_expirada(url_original)
                return True

            return False
        except:
            return False

    def _get_contextual_textarea_response(self, question):
        """Genera respuesta contextual basada en la pregunta del textarea"""
        q = question.lower()

        # Portfolio / reel / link
        if any(w in q for w in ["portfolio", "reel", "link to", "website", "artstation", "demo"]):
            return "Available upon request. I have extensive work samples from 9+ years of Unreal Engine development."

        # Favorite piece / best work
        if any(w in q for w in ["favorite piece", "best work", "proudest", "description of your favorite",
                                 "brief description"]):
            return ("My favorite piece is a real-time ocean simulation system built in Unreal Engine 5 using "
                    "advanced material shaders and Niagara VFX. It features dynamic wave generation, foam particles, "
                    "underwater caustics with Lumen GI, and Nanite-based coastal environments. The system was "
                    "recognized internationally and used by thousands of developers worldwide.")

        # Why did you choose that piece
        if any(w in q for w in ["why did you choose", "why that piece", "why this piece"]):
            return ("I chose this piece because it demonstrates the full breadth of my technical art skills: "
                    "complex material creation, VFX systems, performance optimization, and creative problem-solving. "
                    "It pushed the boundaries of what's possible in real-time rendering and required deep knowledge "
                    "of UE5's rendering pipeline including Nanite, Lumen, and Niagara.")

        # What did you contribute
        if any(w in q for w in ["what did you contribute", "your contribution", "your role in"]):
            return ("I was the sole developer responsible for all aspects: shader/material development, "
                    "Niagara VFX particle systems, Blueprint and C++ programming, performance optimization, "
                    "and the overall technical art direction. I designed the architecture, implemented all systems, "
                    "and optimized for real-time performance across multiple platforms.")

        # How would you improve
        if any(w in q for w in ["how would you improve", "more time", "more resources", "if you could change"]):
            return ("With more time and resources, I would add machine learning-driven wave simulation for "
                    "more realistic ocean behavior, implement a full weather system affecting the water surface, "
                    "add interactive fluid dynamics for gameplay objects, and create a node-based editor for "
                    "artists to customize parameters without touching code.")

        # Anything to clarify / additional info
        if any(w in q for w in ["clarify", "anything else", "additional information", "additional comments",
                                 "anything you would like"]):
            return ("I am based in Santiago, Chile and available for remote work across all time zones. "
                    "I am passionate about game development and committed to delivering high-quality work. "
                    "I am open to contract, full-time, or freelance arrangements.")

        # Gaming experience
        if any(w in q for w in ["gaming experience", "game name", "playing hours", "games you play",
                                 "games you've played"]):
            return DATOS_PERSONALES.get("gaming_experience",
                "Played 500+ hours of AAA games including Fortnite (UE5), Gears of War, Final Fantasy VII Remake. "
                "Active player of competitive FPS and RPG genres.")

        # Why do you want to work here / interest in company
        if any(w in q for w in ["why do you want", "interest in", "why this company", "why this role",
                                 "what attracts you", "motivation"]):
            return ("I am deeply passionate about creating immersive game experiences and have dedicated over 9 years "
                    "to mastering Unreal Engine. I am excited about the opportunity to contribute my technical art "
                    "expertise to a team working on cutting-edge projects. I believe my experience with UE4/UE5, "
                    "including Blueprints, C++, materials, VFX, and optimization, makes me a strong fit.")

        # Experience with specific tools / skills
        if any(w in q for w in ["experience with", "proficiency", "skill", "tools you use"]):
            return ("9+ years with Unreal Engine 4 (4.12-4.27) and UE5 (5.0-5.4). Expert in Blueprints, C++ (UE), "
                    "Materials/Shaders, Niagara VFX, Nanite, Lumen, World Partition. Also proficient in "
                    "Python, HTML/CSS, and React. Experience with performance optimization and real-time simulation.")

        # Recent/exciting project
        if any(w in q for w in ["recent exciting project", "recent project", "exciting project",
                                 "worked on recently", "project you worked on"]):
            return ("I recently built a comprehensive automated job application system in Python using Selenium "
                    "WebDriver. It interacts with 4+ ATS platforms (Greenhouse, Lever, Workable, Ashby), parses "
                    "dynamic web forms, handles cookie banners, uploads files, and fills contextual questions "
                    "intelligently. It processes 400+ listings per run with deduplication and error recovery. "
                    "I'm excited about it because it combines web scraping, automation, and intelligent decision-making.")

        # Python specific questions
        if any(w in q for w in ["python project", "python experience", "complex python",
                                 "hairy python", "python challenge"]):
            return ("I built a comprehensive automated job application system in Python that uses Selenium WebDriver "
                    "to interact with multiple ATS platforms (Greenhouse, Lever, Workable, Ashby). The system parses "
                    "dynamic web forms, handles cookie banners, uploads files, and intelligently fills contextual "
                    "questions. It processes 400+ job listings per run with deduplication and error recovery. "
                    "The challenge was handling diverse form structures across platforms while maintaining reliability.")

        # AI / LLM / ML questions
        if any(w in q for w in ["ai development", "ai tool", "claude", "copilot", "cursor",
                                 "llm", "large language model", "gpt", "fine-tun",
                                 "machine learning", "tensorflow", "scikit", "ml model"]):
            return ("I regularly use Claude Code and GitHub Copilot for development tasks. I have built "
                    "Python automation tools that leverage AI for intelligent form analysis and contextual "
                    "response generation. I have experience integrating AI into development workflows for "
                    "code generation, debugging, and data processing. I am familiar with Python ML libraries "
                    "and have used them for data analysis and pattern recognition tasks.")

        # Salary expectations
        if any(w in q for w in ["salary", "compensation", "pay rate", "hourly rate", "monthly rate",
                                 "salary expectation", "desired salary"]):
            return "Open to discussion based on the role's responsibilities and scope. Preferred currency: USD."

        # Timezone questions
        if any(w in q for w in ["time zone", "timezone", "what timezone", "located in",
                                 "what time zone"]):
            return "CLT (Chile Standard Time, UTC-3). I am flexible and can adapt to other time zones."

        # Comfortable with specific timezone
        if any(w in q for w in ["comfortable working", "eet hours", "est hours", "pst hours",
                                 "cet hours", "gmt hours", "overlap", "work hours"]):
            return "Yes"

        # Start date / notice period / availability
        if any(w in q for w in ["start date", "notice period", "availability", "when can you start",
                                 "earliest start", "available to start"]):
            return "Available immediately. I can start within 1-2 weeks."

        # Where do you live / location details
        if any(w in q for w in ["where do you live", "city / province", "city province",
                                 "current location", "where are you based", "country of residence"]):
            return "Santiago, Región Metropolitana, Chile"

        # Problem solving / debugging / root cause
        if any(w in q for w in ["root cause", "ambiguous", "messy technical", "debugging", "troubleshoot",
                                 "problem solving", "approach to solving"]):
            return ("When facing ambiguous technical problems, I follow a systematic approach: 1) Reproduce "
                    "the issue consistently, 2) Isolate variables by testing components independently, 3) Use "
                    "logging and debugging tools to trace execution flow, 4) Research similar issues in documentation "
                    "and community resources, 5) Implement and test the fix incrementally. For example, in my "
                    "Python automation project, I debugged form submission failures across 4 different ATS platforms "
                    "by analyzing network requests, DOM structures, and timing issues.")

        # QA / Testing specific
        if any(w in q for w in ["testing experience", "qa experience", "bug report", "test case",
                                 "quality assurance", "test plan", "regression"]):
            return ("I have experience in game testing and QA processes. As a developer with 9+ years of UE4/UE5 "
                    "experience, I understand game mechanics deeply and can identify bugs in gameplay, rendering, "
                    "physics, and UI. I have experience writing bug reports, creating test cases, and performing "
                    "regression testing. My strong Python skills allow me to write automated test scripts.")

        # Default: UE experience (but shorter)
        return ("I have 9+ years of experience with Unreal Engine 4 and 5, contributing to internationally "
                "recognized plugins and tools. Expert in Blueprints, C++, Nanite, Lumen, Niagara VFX, "
                "materials/shaders, level design, and performance optimization. Also proficient in Python and HTML/CSS.")

    def _gh_switch_to_form_context(self):
        """Detecta iframes de Greenhouse y cambia el contexto de Selenium si es necesario.
        Retorna True si se cambió a un iframe."""
        iframe_selectors = [
            "iframe#grnhse_iframe",
            "iframe[src*='greenhouse']",
            "iframe[src*='grnh']",
            "iframe[id*='greenhouse']",
            "iframe[name*='greenhouse']",
        ]
        for sel in iframe_selectors:
            try:
                iframes = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for iframe in iframes:
                    if iframe.is_displayed():
                        self.driver.switch_to.frame(iframe)
                        logging.info(f"  Greenhouse: Cambiado a iframe ({sel})")
                        return True
            except:
                continue
        return False

    def _postular_greenhouse(self, url, carta):
        """Handler para Greenhouse ATS (React/Remix rendered forms)"""
        logging.info("  [Plataforma: Greenhouse]")

        # Desactivar implicit_wait temporalmente para evitar conflictos
        self.driver.implicitly_wait(0)
        in_iframe = False

        self.driver.get(url)
        time.sleep(5)

        # Cerrar cookie banners
        self._cerrar_cookie_banners()

        # Detectar y cambiar a iframe de Greenhouse si existe
        in_iframe = self._gh_switch_to_form_context()

        # Verificar si la página está expirada
        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            if in_iframe:
                self.driver.switch_to.default_content()
            self.driver.implicitly_wait(2)
            return False

        # Detectar si es una página general de job board (no oferta individual)
        # Esto pasa cuando: URL redirigió a ?error=true, o la página tiene #keyword-filter
        try:
            current_url = self.driver.current_url
            if "error=true" in current_url:
                logging.info("  OFERTA EXPIRADA - Greenhouse redirigió a error=true")
                guardar_url_expirada(url)
                if in_iframe:
                    self.driver.switch_to.default_content()
                self.driver.implicitly_wait(2)
                return False
            keyword_filter = self.driver.find_elements(By.CSS_SELECTOR, "#keyword-filter")
            if keyword_filter:
                # Es un listado general, no una oferta individual
                logging.info("  PÁGINA GENERAL de Greenhouse detectada (keyword-filter)")
                logging.info("  No es una oferta individual - saltando")
                guardar_url_expirada(url)
                if in_iframe:
                    self.driver.switch_to.default_content()
                self.driver.implicitly_wait(2)
                return False
        except:
            pass

        # Buscar y clickear botón "Apply" (EN/FR/ES)
        try:
            buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Apply')] | //button[contains(text(), 'Postuler')] | "
                "//button[contains(text(), 'Postular')] | //button[contains(text(), 'Candidater')]")
            apply_btn = None
            for btn in buttons:
                btn_text = btn.text.strip()
                if btn.is_displayed() and btn_text in ["Apply", "Postuler", "Postular", "Candidater"]:
                    apply_btn = btn
                    break
            if not apply_btn and buttons:
                for btn in buttons:
                    if btn.is_displayed() and "Submit" not in btn.text and "Soumettre" not in btn.text:
                        apply_btn = btn
                        break

            if apply_btn:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_btn)
                time.sleep(1)
                apply_btn.click()
                logging.info("  Botón Apply clickeado")
                self._esperar_renderizado_spa(timeout=12)
            else:
                logging.info("  No se encontró botón Apply, buscando formulario directo...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._esperar_renderizado_spa(timeout=8)
        except Exception as e:
            logging.info(f"  Error con botón Apply: {e}")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._esperar_renderizado_spa(timeout=8)

        # Detectar idioma
        idioma = self._detectar_idioma_pagina()
        logging.info(f"  Idioma detectado: {idioma.upper()}")

        # Intentar llenar campos directamente (sin WebDriverWait)
        # Greenhouse Remix usa: id="first_name", id="last_name", id="email", id="phone"
        llenado = False

        # Diagnóstico: listar inputs visibles
        all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel']")
        visible_inputs = [i for i in all_inputs if i.is_displayed()]
        logging.info(f"  Inputs visibles encontrados: {len(visible_inputs)}")
        for inp in visible_inputs[:5]:
            logging.info(f"    input: id='{inp.get_attribute('id')}', aria='{inp.get_attribute('aria-label')}'")

        # Multi-strategy field filling con _find_first_match
        campos_gh = [
            (["#first_name", "input[name*='first_name']", "input[autocomplete='given-name']",
              "input[aria-label*='First']", "input[placeholder*='First']"],
             DATOS_PERSONALES["nombre"], "Nombre"),
            (["#last_name", "input[name*='last_name']", "input[autocomplete='family-name']",
              "input[aria-label*='Last']", "input[placeholder*='Last']"],
             DATOS_PERSONALES["apellido"], "Apellido"),
            (["#preferred_name", "input[name*='preferred']", "input[aria-label*='Preferred']"],
             DATOS_PERSONALES["nombre"], "Nombre preferido"),
            (["#email", "input[type='email']", "input[name*='email']", "input[autocomplete='email']",
              "input[aria-label*='Email']", "input[placeholder*='Email']"],
             DATOS_PERSONALES["email"], "Email"),
            (["#phone", "input[type='tel']", "input[name*='phone']", "input[autocomplete='tel']",
              "input[aria-label*='Phone']", "input[placeholder*='Phone']"],
             DATOS_PERSONALES["telefono"], "Teléfono"),
        ]

        for selectors, valor, label in campos_gh:
            elem = self._find_first_match(selectors)
            if elem:
                try:
                    elem.click()
                    time.sleep(0.3)
                    elem.clear()
                    elem.send_keys(valor)
                    logging.info(f"  {label} llenado: {valor[:30]}")
                    llenado = True
                except:
                    logging.info(f"  Error llenando {label}")
            else:
                logging.info(f"  Campo {label} no encontrado")

        # === UBICACIÓN / COUNTRY / CITY ===
        # Greenhouse usa autocomplete para location y dropdown para country
        # Intentar llenar el campo de ubicación (location autocomplete)
        location_filled = False
        for loc_selector in ["#location", "#location_autocomplete", "input[aria-label='Location']",
                             "input[name='location']", "input[placeholder*='city']",
                             "input[placeholder*='City']", "input[placeholder*='location']",
                             "input[aria-label='City']"]:
            try:
                loc_elem = self.driver.find_element(By.CSS_SELECTOR, loc_selector)
                if loc_elem.is_displayed() and loc_elem.is_enabled():
                    loc_elem.click()
                    time.sleep(0.3)
                    loc_elem.clear()
                    loc_elem.send_keys("Santiago, Chile")
                    time.sleep(1)
                    # Seleccionar primera sugerencia del autocomplete si aparece
                    try:
                        suggestions = self.driver.find_elements(By.CSS_SELECTOR,
                            "li[role='option'], .pac-item, .suggestions li, "
                            "[class*='suggestion'], [class*='Suggestion'], "
                            "[class*='autocomplete'] li, [class*='dropdown'] li")
                        for sug in suggestions:
                            if sug.is_displayed():
                                sug.click()
                                location_filled = True
                                logging.info("  Ubicación llenada: Santiago, Chile (autocomplete)")
                                break
                    except:
                        pass
                    if not location_filled:
                        loc_elem.send_keys(Keys.RETURN)
                        location_filled = True
                        logging.info("  Ubicación llenada: Santiago, Chile")
                    break
            except:
                continue

        # Intentar llenar campo Country (puede ser input, select, o React dropdown)
        country_filled = False
        # Primero intentar con select nativo
        try:
            country_select = self.driver.find_element(By.CSS_SELECTOR, "#country")
            tag = country_select.tag_name.lower()
            if tag == "select":
                sel = Select(country_select)
                for opt_text in ["Chile", "CL"]:
                    try:
                        sel.select_by_visible_text(opt_text)
                        country_filled = True
                        logging.info("  País llenado: Chile (select)")
                        break
                    except:
                        continue
            elif tag == "input" and country_select.is_displayed():
                country_select.click()
                time.sleep(0.3)
                country_select.clear()
                country_select.send_keys("Chile")
                time.sleep(1)
                # Seleccionar de autocomplete
                try:
                    opts = self.driver.find_elements(By.CSS_SELECTOR,
                        "li[role='option'], [class*='option'], [class*='suggestion']")
                    for opt in opts:
                        if opt.is_displayed() and "chile" in opt.text.lower():
                            opt.click()
                            country_filled = True
                            logging.info("  País llenado: Chile (autocomplete)")
                            break
                except:
                    pass
                if not country_filled:
                    country_select.send_keys(Keys.RETURN)
                    country_filled = True
                    logging.info("  País llenado: Chile (input)")
        except:
            pass

        # Si no se encontró #country, buscar por otros selectores
        if not country_filled:
            for country_sel in ["select[name*='country']", "select[aria-label*='Country']",
                                "input[aria-label='Country']", "input[name*='country']"]:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, country_sel)
                    if elem.is_displayed():
                        if elem.tag_name.lower() == "select":
                            sel = Select(elem)
                            try:
                                sel.select_by_visible_text("Chile")
                                country_filled = True
                                logging.info("  País llenado: Chile (select fallback)")
                            except:
                                pass
                        else:
                            elem.click()
                            time.sleep(0.3)
                            elem.clear()
                            elem.send_keys("Chile")
                            time.sleep(0.5)
                            elem.send_keys(Keys.RETURN)
                            country_filled = True
                            logging.info("  País llenado: Chile (input fallback)")
                        break
                except:
                    continue

        # Llenar campo de ciudad si existe por separado
        for city_sel in ["#city", "input[name='city']", "input[aria-label='City']",
                         "input[placeholder*='city']", "input[placeholder*='City']"]:
            try:
                city_elem = self.driver.find_element(By.CSS_SELECTOR, city_sel)
                if city_elem.is_displayed() and city_elem.is_enabled():
                    city_elem.click()
                    time.sleep(0.3)
                    city_elem.clear()
                    city_elem.send_keys("Santiago")
                    logging.info("  Ciudad llenada: Santiago")
                    break
            except:
                continue

        # Llenar campos de state/province/address si existen
        for addr_sel, addr_val, addr_label in [
            ("#state", "Región Metropolitana", "Estado/Región"),
            ("input[name='state']", "Región Metropolitana", "Estado/Región"),
            ("input[aria-label='State']", "Región Metropolitana", "Estado/Región"),
            ("#address", "La Florida, Santiago", "Dirección"),
            ("input[name='address']", "La Florida, Santiago", "Dirección"),
        ]:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, addr_sel)
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    time.sleep(0.3)
                    elem.clear()
                    elem.send_keys(addr_val)
                    logging.info(f"  {addr_label} llenado: {addr_val}")
                    break
            except:
                continue

        # LinkedIn y Portfolio - llenar SIEMPRE (muchos formularios lo requieren)
        linkedin_val = DATOS_PERSONALES.get("linkedin", "N/A")
        portfolio_val = DATOS_PERSONALES.get("portfolio", "N/A")
        for selectors, valor, label in [
            (["input[aria-label*='LinkedIn' i]", "input[name*='linkedin' i]", "input[id*='linkedin' i]",
              "input[placeholder*='LinkedIn' i]"], linkedin_val, "LinkedIn"),
            (["input[aria-label*='Portfolio' i]", "input[aria-label*='Website' i]",
              "input[name*='portfolio' i]", "input[name*='website' i]",
              "input[id*='portfolio' i]", "input[placeholder*='Portfolio' i]",
              "input[placeholder*='Website' i]", "input[aria-label*='URL' i]"], portfolio_val, "Portfolio"),
        ]:
            for sel in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.is_displayed() and not (elem.get_attribute("value") or "").strip():
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                        time.sleep(0.3)
                        elem.click()
                        time.sleep(0.2)
                        elem.clear()
                        elem.send_keys(valor)
                        logging.info(f"  {label} llenado: {valor[:30]}")
                        break
                except:
                    continue

        # === LLENAR TODOS LOS SELECTS/DROPDOWNS ===
        try:
            all_selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel_elem in all_selects:
                if not sel_elem.is_displayed():
                    continue
                sel_id = sel_elem.get_attribute("id") or ""
                sel_name = sel_elem.get_attribute("name") or ""
                aria_label = sel_elem.get_attribute("aria-label") or ""
                # También buscar el label asociado
                parent_label = ""
                try:
                    parent = sel_elem.find_element(By.XPATH, "./ancestor::*[contains(@class,'field')]//label")
                    parent_label = parent.text.lower()
                except:
                    pass
                combined = f"{sel_id} {sel_name} {aria_label} {parent_label}".lower()

                if "country" in combined and country_filled:
                    continue

                sel_obj = Select(sel_elem)
                options_text = [o.text.strip() for o in sel_obj.options]
                options_lower = [o.lower() for o in options_text]

                # Country no llenado aún
                if "country" in combined and not country_filled:
                    for opt in options_text:
                        if "chile" in opt.lower():
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  País (select): {opt}")
                            country_filled = True
                            break

                # Autorización de trabajo / legally entitled / eligible / right to work
                elif any(w in combined for w in ["authorized", "authorization", "legally entitled",
                                                  "eligible", "legal right", "right to work",
                                                  "work permit", "permission to work"]):
                    for opt in ["No", "no"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Autorización trabajo = No")
                            break
                        except:
                            continue

                # Sponsorship / visa
                elif any(w in combined for w in ["sponsor", "visa", "sponsorship"]):
                    for opt in ["Yes", "yes"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Sponsorship = Yes")
                            break
                        except:
                            continue

                # Worked for company before? / previously
                elif any(w in combined for w in ["worked for", "previously", "prior", "former"]):
                    for opt in ["No", "no"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Trabajó antes = No")
                            break
                        except:
                            continue

                # Related to employee / relationship
                elif any(w in combined for w in ["related", "relationship", "housing", "relative"]):
                    for opt in ["No", "no"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Relacionado = No")
                            break
                        except:
                            continue

                # Relocation assistance
                elif any(w in combined for w in ["relocation", "relocate"]):
                    for opt in ["No", "no", "Yes", "yes"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Reubicación = {opt}")
                            break
                        except:
                            continue

                # Certifying / acknowledge / confirm
                elif any(w in combined for w in ["certif", "acknowledge", "confirm", "attest", "true and correct"]):
                    for opt in ["Yes", "yes", "I agree", "I acknowledge"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Certificación = {opt}")
                            break
                        except:
                            continue

                # Gender/pronouns
                elif any(w in combined for w in ["gender", "pronoun"]):
                    for opt in ["Prefer not to say", "Decline to self-identify", "Other"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Género = {opt}")
                            break
                        except:
                            continue

                # Race/ethnicity
                elif any(w in combined for w in ["race", "ethnicity", "ethnic"]):
                    for opt in ["Decline to self-identify", "Prefer not to say", "Hispanic or Latino", "Two or more races"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Etnicidad = {opt}")
                            break
                        except:
                            continue

                # Veteran
                elif any(w in combined for w in ["veteran"]):
                    for opt in ["I am not a veteran", "Prefer not to say", "No"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Veterano = {opt}")
                            break
                        except:
                            continue

                # Disability
                elif any(w in combined for w in ["disability", "disabled"]):
                    for opt in ["No, I Don't Have a Disability", "Prefer not to say", "No"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Discapacidad = {opt}")
                            break
                        except:
                            continue

                # Work preference (if it's a select instead of radio)
                elif any(w in combined for w in ["work preference", "work arrangement", "on-site", "remote preference"]):
                    for opt in options_text:
                        if "remote" in opt.lower():
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Preferencia trabajo = {opt}")
                            break

                # Citizenship / residency (Singapore, US, etc)
                elif any(w in combined for w in ["citizen", "residency", "permanent resid", "singapor"]):
                    for opt in ["No", "no", "Non-Citizen", "Neither"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Ciudadanía/Residencia = {opt}")
                            break
                        except:
                            continue

                # Currently interviewing / applying elsewhere
                elif any(w in combined for w in ["currently interview", "interviewing with", "applying"]):
                    for opt in ["No", "no"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Entrevistando actualmente = No")
                            break
                        except:
                            continue

                # Open to reassignment / other roles
                elif any(w in combined for w in ["reassign", "other role", "open to", "consider other"]):
                    for opt in ["Yes", "yes"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Abierto a otros roles = Yes")
                            break
                        except:
                            continue

                # Full-time / employment type
                elif any(w in combined for w in ["full-time", "full time", "employment type", "part-time"]):
                    for opt in options_text:
                        if "yes" in opt.lower() or "full" in opt.lower():
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Tipo empleo = {opt}")
                            break

                # On-site / in-office / hybrid
                elif any(w in combined for w in ["on-site", "onsite", "in-office", "in office", "hybrid"]):
                    for opt in options_text:
                        if "yes" in opt.lower() or "remote" in opt.lower() or "open" in opt.lower():
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Presencial = {opt}")
                            break

                # Age / 18+
                elif any(w in combined for w in ["age", "18 years", "18 or older", "legal age"]):
                    for opt in ["Yes", "yes"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Mayor de edad = Yes")
                            break
                        except:
                            continue

                # Level design tools / software / tools
                elif any(w in combined for w in ["level design tool", "software", "tools used", "primary tool"]):
                    for opt in options_text:
                        if any(w in opt.lower() for w in ["unreal", "ue4", "ue5"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Herramienta = {opt}")
                            break
                    else:
                        # Si no hay opcion UE, seleccionar la primera no-placeholder
                        for opt in options_text:
                            if opt.strip() and opt not in ["Select...", "", "-- Select --", "Please select"]:
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Herramienta (fallback) = {opt}")
                                break

                # Salary range (if select)
                elif any(w in combined for w in ["salary", "compensation", "pay range", "pay expectation"]):
                    # Seleccionar la primera opcion real
                    for opt in options_text:
                        if opt.strip() and opt not in ["Select...", "", "-- Select --", "Please select"]:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Salario (select) = {opt}")
                            break

                # Notice period / availability / start date
                elif any(w in combined for w in ["notice period", "notice", "availability", "start date",
                                                  "when can you start", "earliest start"]):
                    # Try immediate/ASAP first, then shortest option
                    for opt in options_text:
                        opt_l = opt.lower()
                        if any(w in opt_l for w in ["immediate", "asap", "right away", "0", "none",
                                                     "less than", "1 week", "2 week", "available now"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Periodo aviso = {opt}")
                            break
                    else:
                        # Pick first non-placeholder
                        for opt in options_text:
                            if opt.strip() and opt not in ["Select...", "", "-- Select --", "Please select", "Select"]:
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Periodo aviso (fallback) = {opt}")
                                break

                # How did you hear about us (select version)
                elif any(w in combined for w in ["how did you hear", "hear about", "how did you find",
                                                  "source", "referral source"]):
                    for opt in options_text:
                        opt_l = opt.lower()
                        if any(w in opt_l for w in ["online", "internet", "job board", "job search",
                                                     "website", "career", "google", "indeed", "linkedin"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Fuente (select) = {opt}")
                            break
                    else:
                        # Pick first non-placeholder (usually "Online Job Board" or similar)
                        for opt in options_text:
                            if opt.strip() and opt not in ["Select...", "", "-- Select --", "Please select", "Select"]:
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Fuente (select fallback) = {opt}")
                                break

                # Province / State / Region
                elif any(w in combined for w in ["province", "state", "region"]):
                    # Try to find anything related to international/other
                    for opt in options_text:
                        opt_l = opt.lower()
                        if any(w in opt_l for w in ["other", "international", "outside", "n/a", "not applicable"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Provincia/Estado = {opt}")
                            break
                    else:
                        for opt in options_text:
                            if opt.strip() and opt not in ["Select...", "", "-- Select --", "Please select", "Select"]:
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Provincia/Estado (fallback) = {opt}")
                                break

                # Data transfer / GDPR consent (select)
                elif any(w in combined for w in ["data transfer", "data processing", "gdpr", "privacy",
                                                  "consent to transfer", "point of data"]):
                    for opt in ["Yes", "yes", "I agree", "I consent", "Accept"]:
                        try:
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Consentimiento datos = {opt}")
                            break
                        except:
                            continue

                # AGGRESSIVE FALLBACK: Any select still at "Select..." - pick first real option
                else:
                    try:
                        current = sel_obj.first_selected_option.text.strip()
                        if current in ["Select...", "", "-- Select --", "Please select", "Select"]:
                            # Try common safe defaults first
                            for safe in ["No", "no", "Yes", "yes", "Prefer not to say",
                                         "Decline to self-identify", "N/A"]:
                                try:
                                    sel_obj.select_by_visible_text(safe)
                                    logging.info(f"  Select fallback '{combined[:30]}' = {safe}")
                                    break
                                except:
                                    continue
                            else:
                                # Last resort: pick first non-placeholder option
                                for opt in options_text:
                                    if opt.strip() and opt not in ["Select...", "", "-- Select --", "Please select", "Select"]:
                                        sel_obj.select_by_visible_text(opt)
                                        logging.info(f"  Select ultimo fallback '{combined[:30]}' = {opt}")
                                        break
                    except:
                        pass
        except Exception as e:
            logging.info(f"  Error llenando dropdowns: {e}")

        # === LLENAR DROPDOWNS REACT (Greenhouse custom selects) ===
        # Greenhouse usa componentes React Select que NO son <select> HTML nativos
        # Son divs con clases CSS como css-*-control, y se abren al hacer click
        try:
            # Buscar todos los contenedores de campos custom de Greenhouse
            # Greenhouse envuelve cada pregunta custom en un div con data-question o similar
            custom_fields = self.driver.find_elements(By.CSS_SELECTOR,
                "[class*='select__control'], [class*='css-'][class*='-control'], "
                "[role='combobox'], [class*='Select-control']")

            for field in custom_fields:
                if not field.is_displayed():
                    continue
                # Verificar si ya tiene un valor seleccionado (no "Select...")
                try:
                    current_text = field.text.strip()
                    if current_text and current_text not in ["Select...", "Select", "-- Select --", ""]:
                        continue  # Ya tiene valor
                except:
                    pass

                # Obtener el label/pregunta asociada
                question = ""
                try:
                    # Buscar el label más cercano (padre o hermano anterior)
                    parent = field.find_element(By.XPATH, "./ancestor::*[contains(@class,'field')]")
                    labels = parent.find_elements(By.CSS_SELECTOR, "label, [class*='label'], legend")
                    if labels:
                        question = labels[0].text.strip().lower()
                except:
                    try:
                        prev_label = field.find_element(By.XPATH, "./preceding::label[1]")
                        question = prev_label.text.strip().lower()
                    except:
                        pass

                if not question:
                    continue

                # Determinar la respuesta correcta basada en la pregunta
                answer = None
                if any(w in question for w in ["how did you hear", "hear about", "how did you find"]):
                    answer = ["Online Job Search", "Internet", "Job Board", "Website", "Google", "LinkedIn", "Other"]
                elif any(w in question for w in ["sponsor", "visa"]):
                    answer = ["Yes", "yes"]
                elif any(w in question for w in ["18 year", "18 or older", "at least 18"]):
                    answer = ["Yes", "yes"]
                elif any(w in question for w in ["authorized", "authorised", "legally", "right to work", "permission to work"]):
                    answer = ["No", "no"]  # No autorizado a trabajar en ese país
                elif any(w in question for w in ["relocat"]):
                    answer = ["Yes", "yes"]
                elif any(w in question for w in ["gender"]):
                    answer = ["Prefer not to say", "Decline to Self-Identify", "Prefer not to disclose", "Other"]
                elif any(w in question for w in ["pronoun"]):
                    answer = ["Prefer not to say", "They/Them", "Other"]
                elif any(w in question for w in ["sexual orientation"]):
                    answer = ["Prefer not to say", "Decline to Self-Identify", "Other"]
                elif any(w in question for w in ["hispanic", "latinx", "latino"]):
                    answer = ["Yes", "Hispanic or Latino", "yes"]
                elif any(w in question for w in ["race", "ethnicity"]):
                    answer = ["Decline to Self-Identify", "Prefer not to say", "Hispanic or Latino", "Two or More Races"]
                elif any(w in question for w in ["veteran"]):
                    answer = ["I am not a protected veteran", "Prefer not to say", "No"]
                elif any(w in question for w in ["disability", "disabled"]):
                    answer = ["Prefer not to say", "No, I Don't Have a Disability", "No"]
                elif any(w in question for w in ["high school", "diploma", "ged", "equivalency"]):
                    answer = ["Yes", "yes"]
                elif any(w in question for w in ["data privacy", "privacy consent", "privacy notice", "acknowledge"]):
                    answer = ["Yes", "I agree", "I acknowledge", "yes"]
                elif any(w in question for w in ["background check", "pre-employment"]):
                    answer = ["Yes", "I agree", "I acknowledge", "yes"]
                elif any(w in question for w in ["citizen", "residency", "permanent resid"]):
                    answer = ["No", "no"]
                elif any(w in question for w in ["interview", "currently apply"]):
                    answer = ["No", "no"]
                elif any(w in question for w in ["notice period"]):
                    answer = ["Immediately", "Less than 2 weeks", "2 weeks"]
                elif any(w in question for w in ["work authorization", "require work"]):
                    answer = ["Yes", "yes"]
                else:
                    # Fallback genérico
                    answer = ["No", "Yes", "Prefer not to say", "N/A"]

                if not answer:
                    continue

                # Intentar hacer click en el dropdown para abrirlo
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
                    time.sleep(0.3)
                    field.click()
                    time.sleep(0.5)

                    # Buscar las opciones del menu desplegable
                    options = self.driver.find_elements(By.CSS_SELECTOR,
                        "[class*='option'], [role='option'], [class*='menu'] [class*='option']")

                    if not options:
                        time.sleep(0.5)
                        options = self.driver.find_elements(By.CSS_SELECTOR,
                            "[class*='option'], [role='option'], [id*='option']")

                    selected = False
                    for desired in answer:
                        for opt in options:
                            if opt.is_displayed() and desired.lower() in opt.text.strip().lower():
                                opt.click()
                                logging.info(f"  React Select '{question[:40]}' = {opt.text.strip()[:30]}")
                                selected = True
                                break
                        if selected:
                            break

                    if not selected and options:
                        # Click primera opción visible que no sea placeholder
                        for opt in options:
                            opt_text = opt.text.strip()
                            if opt.is_displayed() and opt_text and opt_text not in ["Select...", "Select", ""]:
                                opt.click()
                                logging.info(f"  React Select fallback '{question[:40]}' = {opt_text[:30]}")
                                break
                        else:
                            # Cerrar el dropdown sin seleccionar
                            try:
                                self.driver.find_element(By.TAG_NAME, "body").click()
                            except:
                                pass

                    time.sleep(0.3)
                except Exception as e:
                    logging.info(f"  Error React Select '{question[:30]}': {e}")
                    try:
                        self.driver.find_element(By.TAG_NAME, "body").click()
                    except:
                        pass
        except Exception as e:
            logging.info(f"  Error llenando React dropdowns: {e}")

        # === LLENAR INPUTS DE TEXTO ADICIONALES (título, empresa, salario, dirección, etc.) ===
        try:
            all_text_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                "input[type='text'], input[type='url'], input[type='number'], input:not([type])")
            for inp in all_text_inputs:
                if not inp.is_displayed() or not inp.is_enabled():
                    continue
                inp_id = (inp.get_attribute("id") or "").lower()
                inp_name = (inp.get_attribute("name") or "").lower()
                inp_aria = (inp.get_attribute("aria-label") or "").lower()
                inp_placeholder = (inp.get_attribute("placeholder") or "").lower()
                combined_inp = f"{inp_id} {inp_name} {inp_aria} {inp_placeholder}"

                # Saltar campos ya llenados
                current_val = inp.get_attribute("value") or ""
                if current_val.strip():
                    continue

                # Saltar campos base ya manejados
                if inp_id in ["first_name", "last_name", "email", "phone", "country"]:
                    continue

                # Scroll antes de click para evitar intercepción
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
                    time.sleep(0.2)
                except:
                    pass

                # Preferred name / preferred first name / preferred last name
                if any(w in combined_inp for w in ["preferred_name", "preferred name", "preferred_first",
                                                     "preferred_last", "preferred last", "preferred first"]):
                    if any(w in combined_inp for w in ["last", "apellido", "surname", "family"]):
                        inp.click()
                        time.sleep(0.2)
                        inp.send_keys(DATOS_PERSONALES.get("apellido", "Sepulveda"))
                        logging.info("  Preferred last name llenado")
                    else:
                        inp.click()
                        time.sleep(0.2)
                        inp.send_keys(DATOS_PERSONALES.get("nombre", "Ricardo"))
                        logging.info("  Preferred first name llenado")

                # Postal code / zip code
                elif any(w in combined_inp for w in ["postal code", "zip code", "zipcode", "zip", "postal"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("8240000")
                    logging.info("  Código postal llenado")

                # City (text input version)
                elif any(w in combined_inp for w in ["city"]) and "country" not in combined_inp:
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Santiago")
                    logging.info("  Ciudad llenada")

                # Phone number (if not filled by base handler)
                elif any(w in combined_inp for w in ["phone", "telephone", "mobile", "cell"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys(DATOS_PERSONALES.get("telefono", "+1234567890"))
                    logging.info("  Teléfono adicional llenado")

                # Título actual / current title
                elif any(w in combined_inp for w in ["current title", "job title", "current position"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Game Developer | Unreal Engine 4 & 5")
                    logging.info("  Título actual llenado")

                # Empresa actual / current company
                elif any(w in combined_inp for w in ["current company", "current employer", "company name"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Independent Game Developer")
                    logging.info("  Empresa actual llenada")

                # Salario / salary
                elif any(w in combined_inp for w in ["salary", "compensation", "pay expectation"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Open to discussion / Negotiable")
                    logging.info("  Salario llenado")

                # Dirección completa / full address
                elif any(w in combined_inp for w in ["full address", "street address", "address line"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("La Florida, Santiago, Chile")
                    logging.info("  Dirección completa llenada")

                # How did you hear / referral source
                elif any(w in combined_inp for w in ["how did you hear", "hear about", "source", "referral"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Online job search")
                    logging.info("  Fuente de búsqueda llenada")

                # Graduation year
                elif any(w in combined_inp for w in ["graduation", "grad year", "year of graduation"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys(DATOS_PERSONALES.get("graduation_year", "2016"))
                    logging.info("  Año graduación llenado")

                # Current location (not country/city specific)
                elif any(w in combined_inp for w in ["current location", "your location", "enter your location"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Santiago, Chile")
                    time.sleep(1)
                    # Try autocomplete suggestion
                    try:
                        suggestions = self.driver.find_elements(By.CSS_SELECTOR,
                            "li[role='option'], [class*='suggestion'], [class*='option']")
                        for sug in suggestions:
                            if sug.is_displayed() and "santiago" in sug.text.lower():
                                sug.click()
                                break
                        else:
                            inp.send_keys(Keys.RETURN)
                    except:
                        inp.send_keys(Keys.RETURN)
                    logging.info("  Ubicación actual llenada: Santiago, Chile")

                # Website URL / GitHub / Portfolio (generic)
                elif any(w in combined_inp for w in ["website url", "github", "portfolio url",
                                                       "personal website", "url"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys(DATOS_PERSONALES.get("portfolio", "N/A"))
                    logging.info("  Website/URL llenado")

                # Date of birth (for visa purposes)
                elif any(w in combined_inp for w in ["date of birth", "birth date", "dob"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("1990-01-01")
                    logging.info("  Fecha nacimiento llenada")

                # Place of birth
                elif any(w in combined_inp for w in ["place of birth", "birth place", "birthplace"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Santiago, Chile")
                    logging.info("  Lugar nacimiento llenado")

        except Exception as e:
            logging.info(f"  Error llenando inputs adicionales: {e}")

        # === RADIO BUTTONS (work preference, work authorization, etc.) ===
        try:
            # Agrupar radio buttons por nombre para saber cuáles son del mismo grupo
            radio_groups = {}
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for radio in radios:
                if not radio.is_displayed():
                    continue
                group_name = radio.get_attribute("name") or "unknown"
                if group_name not in radio_groups:
                    radio_groups[group_name] = []
                radio_label = ""
                try:
                    lbl = radio.find_element(By.XPATH, "./following-sibling::*|./parent::label")
                    radio_label = lbl.text.strip().lower()
                except:
                    radio_label = (radio.get_attribute("value") or "").lower()
                radio_groups[group_name].append((radio, radio_label))

            for group_name, group_radios in radio_groups.items():
                # Verificar si alguno ya está seleccionado
                if any(r.is_selected() for r, _ in group_radios):
                    continue

                all_labels = " ".join(label for _, label in group_radios)

                # Work preference: Remote
                if any(w in all_labels for w in ["full remote", "remote", "fully remote"]):
                    for radio, label in group_radios:
                        if any(w in label for w in ["full remote", "remote", "fully remote"]):
                            radio.click()
                            logging.info(f"  Radio: Remote seleccionado")
                            break

                # Work authorization: "Yes - I will require sponsorship"
                elif any(w in all_labels for w in ["require work authorization", "sponsorship", "work authorization"]):
                    for radio, label in group_radios:
                        if "yes" in label and "require" in label:
                            radio.click()
                            logging.info(f"  Radio: Work authorization = Yes require")
                            break
                    else:
                        # Si no hay "yes require", seleccionar el segundo (usualmente "Yes")
                        if len(group_radios) >= 2:
                            group_radios[1][0].click()
                            logging.info(f"  Radio: Work auth fallback = {group_radios[1][1][:30]}")

                # Certify / acknowledge / confirm
                elif any(w in all_labels for w in ["certif", "acknowledge", "confirm", "agree"]):
                    for radio, label in group_radios:
                        if any(w in label for w in ["yes", "agree", "confirm", "acknowledge"]):
                            radio.click()
                            logging.info(f"  Radio: Certificación = {label[:30]}")
                            break
        except:
            pass

        # === CHECKBOXES (consent, privacy, acknowledgement) ===
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                if not cb.is_displayed():
                    continue
                cb_id = (cb.get_attribute("id") or "").lower()
                cb_name = (cb.get_attribute("name") or "").lower()
                cb_label = ""
                try:
                    lbl = cb.find_element(By.XPATH, "./ancestor::label | ./following-sibling::label | ./parent::*/label")
                    cb_label = lbl.text.lower()
                except:
                    pass
                # Also try to get label via for attribute or parent div text
                if not cb_label:
                    try:
                        cb_for_id = cb.get_attribute("id")
                        if cb_for_id:
                            lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_for_id}']")
                            cb_label = lbl.text.lower()
                    except:
                        pass
                if not cb_label:
                    try:
                        parent = cb.find_element(By.XPATH, "./parent::*")
                        cb_label = parent.text.lower()[:100]
                    except:
                        pass
                combined_cb = f"{cb_id} {cb_name} {cb_label}"
                if any(w in combined_cb for w in ["consent", "privacy", "acknowledge", "agree",
                                                    "certif", "data", "retain", "gdpr", "policy",
                                                    "confirm", "accept", "terms", "i have read",
                                                    "understand", "authorize", "true and correct"]):
                    if not cb.is_selected():
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
                            time.sleep(0.2)
                            cb.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", cb)
                        logging.info(f"  Checkbox aceptado: {combined_cb[:50]}")
        except:
            pass

        # Subir CV usando #resume
        cv_path = DATOS_PERSONALES.get("cv_path_en", DATOS_PERSONALES["cv_path"]) if idioma == "en" else DATOS_PERSONALES["cv_path"]
        try:
            resume_input = self.driver.find_element(By.CSS_SELECTOR, "#resume")
            resume_input.send_keys(cv_path)
            logging.info(f"  CV subido ({idioma.upper()}): {os.path.basename(cv_path)}")
            llenado = True
            time.sleep(2)
        except:
            self.driver.implicitly_wait(2)
            self._subir_cv(idioma)
            self.driver.implicitly_wait(0)

        # Cover letter
        try:
            cover_input = self.driver.find_element(By.CSS_SELECTOR, "#cover_letter")
            if cover_input.get_attribute("type") == "file":
                carta_path = os.path.join(WORK_DIR, "cover_letter_temp.txt")
                with open(carta_path, "w", encoding="utf-8") as f:
                    f.write(carta)
                cover_input.send_keys(carta_path)
                logging.info("  Cover letter subida")
                time.sleep(1)
        except:
            self.driver.implicitly_wait(2)
            self._escribir_carta(carta)
            self.driver.implicitly_wait(0)

        # Responder preguntas tipo textarea con respuestas CONTEXTUALES
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        for ta in textareas:
            try:
                if ta.is_displayed() and ta.is_enabled():
                    aria = ta.get_attribute("aria-label") or ""
                    ta_id = ta.get_attribute("id") or ""
                    ta_name = ta.get_attribute("name") or ""
                    if "recaptcha" in ta_id:
                        continue
                    # Skip already filled
                    if (ta.get_attribute("value") or "").strip():
                        continue
                    question = f"{aria} {ta_name}".lower()
                    # Skip cover letter textareas (already handled)
                    if any(w in question for w in ["cover letter", "cover_letter", "carta"]):
                        continue
                    response = self._get_contextual_textarea_response(question)
                    if response:
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ta)
                        time.sleep(0.3)
                        ta.clear()
                        ta.send_keys(response)
                        logging.info(f"  Pregunta respondida: {aria[:60]}")
            except:
                continue

        # Restaurar implicit_wait
        self.driver.implicitly_wait(2)

        # Pre-submit validation: verificar que name y email están llenados
        if not llenado:
            logging.info("  Greenhouse: campos base no llenados, intentando _analizar_y_llenar_pagina...")
            llenado = self._analizar_y_llenar_pagina(carta)

        if llenado:
            time.sleep(1)
            url_antes = self.driver.current_url
            # Try multiple submit button patterns (EN, FR, ES)
            submit_xpaths = [
                "//button[contains(text(), 'Submit application')]",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Soumettre')]",
                "//button[contains(text(), 'Envoyer')]",
                "//button[contains(text(), 'Enviar')]",
                "//button[contains(text(), 'Postular')]",
                "//button[@type='submit']",
                "//input[@type='submit']",
            ]
            for xpath in submit_xpaths:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, xpath)
                    if submit_btn.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
                        time.sleep(1)
                        submit_btn.click()
                        time.sleep(5)
                        resultado = self._verificar_submit(url_antes)
                        if resultado is True:
                            logging.info("  POSTULACIÓN GREENHOUSE EXITOSA Y VERIFICADA!")
                            if in_iframe:
                                self.driver.switch_to.default_content()
                            return True
                        elif resultado is False:
                            logging.warning("  Greenhouse submit falló - errores detectados")
                            if in_iframe:
                                self.driver.switch_to.default_content()
                            return False
                        else:
                            logging.info("  Formulario enviado (sin confirmación explícita)")
                            if in_iframe:
                                self.driver.switch_to.default_content()
                            return True
                except:
                    continue
            logging.info("  No se encontró botón Submit con patrones conocidos, intentando genérico...")
            result = self._hacer_submit()
            if in_iframe:
                self.driver.switch_to.default_content()
            return result
        if in_iframe:
            self.driver.switch_to.default_content()
        return False

    def _postular_lever(self, url, carta):
        """Handler para Lever ATS"""
        logging.info("  [Plataforma: Lever]")

        # Lever: ir directamente a /apply si no está ya
        apply_url = url.rstrip("/")
        if not apply_url.endswith("/apply"):
            apply_url += "/apply"

        self.driver.get(apply_url)
        time.sleep(4)

        # Cerrar cookie banners / overlays que bloquean el formulario
        self._cerrar_cookie_banners()

        # Verificar si la página está expirada
        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # Esperar a que cargue el formulario
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[name='name'], input[name='email'], .application-form, "
                    "form, input[type='text'], input[type='email']"
                ))
            )
            logging.info("  Lever: Formulario detectado")
        except:
            logging.info("  Lever: Esperando carga adicional...")
            time.sleep(3)

        # Detectar idioma
        idioma = self._detectar_idioma_pagina()
        logging.info(f"  Idioma detectado: {idioma.upper()}")

        # Intentar llenar campos específicos de Lever primero
        campos_llenados = 0

        # Lever usa 'name' como campo de nombre completo - multi-strategy
        lever_campos = [
            (["input[name='name']", "input[placeholder*='Full name']", "input[autocomplete='name']",
              "input[aria-label*='Full name']", "input[aria-label*='Name']"],
             DATOS_PERSONALES["nombre_completo"], "nombre_completo"),
            (["input[name='email']", "input[type='email']", "input[autocomplete='email']",
              "input[aria-label*='Email']"],
             DATOS_PERSONALES["email"], "email"),
            (["input[name='phone']", "input[type='tel']", "input[autocomplete='tel']",
              "input[aria-label*='Phone']"],
             DATOS_PERSONALES["telefono"], "telefono"),
            (["input[name='org']", "input[placeholder*='Current company']",
              "input[aria-label*='Current company']", "input[aria-label*='Organization']"],
             "Independent Game Developer", "empresa"),
            (["input[name='urls[LinkedIn]']", "input[placeholder*='LinkedIn']",
              "input[aria-label*='LinkedIn']"],
             DATOS_PERSONALES.get("linkedin", ""), "linkedin"),
            (["input[name='urls[Portfolio]']", "input[placeholder*='Portfolio']",
              "input[aria-label*='Portfolio']", "input[aria-label*='Website']"],
             DATOS_PERSONALES.get("portfolio", ""), "portfolio"),
        ]

        for selectors, valor, nombre in lever_campos:
            if not valor:
                continue
            campo = self._find_first_match(selectors)
            if campo:
                try:
                    campo.click()
                    time.sleep(0.3)
                    campo.clear()
                    campo.send_keys(valor)
                    logging.info(f"  Lever: {nombre} llenado: {valor[:30]}...")
                    campos_llenados += 1
                except:
                    pass

        # Ubicación (Lever usa 'location')
        try:
            loc_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='location']")
            if loc_field.is_displayed():
                loc_field.click()
                time.sleep(0.3)
                loc_field.clear()
                loc_field.send_keys(f"{DATOS_PERSONALES['ciudad']}, {DATOS_PERSONALES['pais']}")
                logging.info("  Lever: ubicacion llenada")
                campos_llenados += 1
                time.sleep(1)
                # Cerrar dropdown de sugerencias si aparece
                loc_field.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
        except:
            pass

        # Si no se llenaron con selectores Lever, usar handler genérico + fallback inteligente
        if campos_llenados == 0:
            logging.info("  Lever: Campos específicos no encontrados, usando handler genérico...")
            if self._llenar_campos_comunes(carta):
                time.sleep(1)
                return self._hacer_submit()
            # Segundo fallback: análisis inteligente de página
            logging.info("  Lever: Handler genérico falló, intentando análisis inteligente...")
            if self._analizar_y_llenar_pagina(carta):
                time.sleep(1)
                return self._hacer_submit()
            return False

        # Subir CV
        self._subir_cv(idioma)

        # Carta de presentación
        self._escribir_carta(carta)

        # Preguntas adicionales (textareas sin valor) - respuestas contextuales
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        for ta in textareas:
            try:
                if ta.is_displayed() and ta.is_enabled():
                    current_val = ta.get_attribute("value") or ""
                    if not current_val.strip():
                        name = ta.get_attribute("name") or ""
                        aria = ta.get_attribute("aria-label") or ""
                        # Also check parent label/heading for context
                        parent_label = ""
                        try:
                            card = ta.find_element(By.XPATH, "./ancestor::*[contains(@class,'card') or contains(@class,'field') or contains(@class,'question')]")
                            parent_label = card.text.strip()[:200].lower()
                        except:
                            pass
                        question = f"{name} {aria} {parent_label}".lower()
                        if "cover" in question or "carta" in question:
                            continue
                        # Skip "how did you hear" textareas - answer with short response
                        if any(w in question for w in ["how did you hear", "hear about", "how did you find",
                                                        "referral source", "source of application"]):
                            ta.send_keys("Online job search")
                            logging.info(f"  Lever: 'How did you hear' textarea respondida")
                            continue
                        response = self._get_contextual_textarea_response(question)
                        ta.send_keys(response)
                        logging.info(f"  Lever: Pregunta adicional respondida ({name})")
            except:
                continue

        # === LEVER: Llenar campos de texto adicionales (desired start date, etc.) ===
        try:
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                "input[type='text'], input[type='date'], input:not([type])")
            for inp in text_inputs:
                if not inp.is_displayed() or not inp.is_enabled():
                    continue
                current_val = (inp.get_attribute("value") or "").strip()
                if current_val:
                    continue
                inp_name = (inp.get_attribute("name") or "").lower()
                inp_placeholder = (inp.get_attribute("placeholder") or "").lower()

                # Multiple strategies to find the label/question text
                parent_text = ""
                # Strategy 1: ancestor with known class
                try:
                    card = inp.find_element(By.XPATH,
                        "./ancestor::*[contains(@class,'card') or contains(@class,'field') "
                        "or contains(@class,'question') or contains(@class,'application')]")
                    parent_text = card.text.strip()[:200].lower()
                except:
                    pass
                # Strategy 2: preceding label element
                if not parent_text:
                    try:
                        parent_text = inp.find_element(By.XPATH, "./preceding::label[1]").text.strip().lower()
                    except:
                        pass
                # Strategy 3: parent div > label or span
                if not parent_text:
                    try:
                        parent_div = inp.find_element(By.XPATH, "./..")
                        parent_text = parent_div.text.strip()[:200].lower()
                    except:
                        pass
                # Strategy 4: grandparent div text
                if not parent_text:
                    try:
                        grandparent = inp.find_element(By.XPATH, "./../..")
                        parent_text = grandparent.text.strip()[:200].lower()
                    except:
                        pass
                # Strategy 5: use JS to get all preceding text
                if not parent_text:
                    try:
                        parent_text = self.driver.execute_script("""
                            var el = arguments[0];
                            var parent = el.closest('.application-question, .custom-question, .field, [class*="question"]');
                            if (parent) return parent.textContent.substring(0, 200);
                            parent = el.parentElement;
                            while (parent && parent.tagName !== 'BODY') {
                                var label = parent.querySelector('label, legend, [class*="label"]');
                                if (label) return label.textContent.substring(0, 200);
                                parent = parent.parentElement;
                            }
                            return '';
                        """, inp).lower()
                    except:
                        pass

                combined = f"{inp_name} {inp_placeholder} {parent_text}"
                logging.info(f"  Lever text input debug: name={inp_name[:30]}, context={parent_text[:60]}")

                # Skip already handled basic fields
                if any(w in inp_name for w in ["name", "email", "phone", "org"]):
                    continue
                # Handle URL fields specifically
                if "url" in inp_name:
                    if "linkedin" in inp_name:
                        linkedin_url = DATOS_PERSONALES.get("linkedin", "")
                        if linkedin_url:
                            inp.click()
                            time.sleep(0.2)
                            inp.send_keys(linkedin_url)
                            logging.info("  Lever: LinkedIn URL llenado")
                    # Skip other URL fields (twitter, github, portfolio) if empty
                    continue
                # Handle location field
                if "location" in inp_name:
                    if not current_val:
                        inp.click()
                        time.sleep(0.2)
                        inp.send_keys(f"{DATOS_PERSONALES['ciudad']}, {DATOS_PERSONALES['pais']}")
                        logging.info("  Lever: Location llenado")
                    continue
                # Desired start date
                if any(w in combined for w in ["start date", "fecha", "when can you", "earliest start",
                                                "date available", "availability date", "desired start"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Immediately / As soon as possible")
                    logging.info("  Lever: Start date llenado")
                # Salary expectations
                elif any(w in combined for w in ["salary", "compensation", "pay", "expected salary"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Open to discussion / Negotiable")
                    logging.info("  Lever: Salary llenado")
                # How did you hear (text version)
                elif any(w in combined for w in ["how did you hear", "hear about", "referral"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Online job search")
                    logging.info("  Lever: How did you hear llenado")
                # Timezone
                elif any(w in combined for w in ["time zone", "timezone", "what timezone"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("CLT (Chile Standard Time, UTC-3)")
                    logging.info("  Lever: Timezone llenado")
                # City/province/country detailed location
                elif any(w in combined for w in ["city / province", "city province", "where do you live",
                                                   "country of residence"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Santiago, Región Metropolitana, Chile")
                    logging.info("  Lever: Detailed location llenado")
                # Notice period
                elif any(w in combined for w in ["notice period", "preferred start"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Available immediately, can start within 1-2 weeks")
                    logging.info("  Lever: Notice period llenado")
                # Salary monthly
                elif any(w in combined for w in ["salary expectations per month", "monthly salary",
                                                   "rate per month"]):
                    inp.click()
                    time.sleep(0.2)
                    inp.send_keys("Open to discussion. Preferred currency: USD")
                    logging.info("  Lever: Monthly salary llenado")
                # Portfolio / website URL (if not in name already)
                elif any(w in combined for w in ["portfolio", "website", "artstation", "github"]):
                    portfolio = DATOS_PERSONALES.get("portfolio", "")
                    if portfolio:
                        inp.click()
                        time.sleep(0.2)
                        inp.send_keys(portfolio)
                        logging.info("  Lever: Portfolio/website llenado")
                # Catch-all: fill any remaining empty text input with contextual response
                else:
                    response = self._get_contextual_textarea_response(combined)
                    if response:
                        inp.click()
                        time.sleep(0.2)
                        inp.send_keys(response)
                        logging.info(f"  Lever: Campo genérico llenado ({inp_name[:30]})")
        except Exception as e:
            logging.info(f"  Lever text input error: {e}")

        # === LEVER: Catch-all - find any remaining empty required fields ===
        try:
            remaining_empty = self.driver.find_elements(By.CSS_SELECTOR,
                "input[type='text']:not([readonly]), textarea:not([readonly])")
            for field in remaining_empty:
                try:
                    if not field.is_displayed() or not field.is_enabled():
                        continue
                    val = (field.get_attribute("value") or "").strip()
                    if val:
                        continue
                    field_name = (field.get_attribute("name") or "").lower()
                    field_placeholder = (field.get_attribute("placeholder") or "").lower()
                    # Skip cover letter
                    if "cover" in field_name or "cover" in field_placeholder:
                        continue
                    # Skip already handled
                    if any(w in field_name for w in ["name", "email", "phone"]):
                        continue
                    # Get context from parent elements
                    context = ""
                    try:
                        parent = field.find_element(By.XPATH, "./ancestor::*[contains(@class,'field') or contains(@class,'question') or contains(@class,'card')]")
                        context = parent.text.strip()[:300].lower()
                    except:
                        try:
                            context = field.find_element(By.XPATH, "./../..").text.strip()[:200].lower()
                        except:
                            pass
                    if context:
                        response = self._get_contextual_textarea_response(context)
                        field.click()
                        time.sleep(0.2)
                        field.send_keys(response)
                        logging.info(f"  Lever: Campo vacío restante llenado ({field_name[:30]})")
                except:
                    continue
        except Exception as e:
            logging.debug(f"  Lever catch-all error: {e}")

        # === LEVER: Radio buttons (work eligibility, pronouns, gender, age) ===
        # Note: Lever hides actual <input type="radio"> and uses styled labels,
        # so we must NOT filter by is_displayed() and must click via JS or click labels
        try:
            radio_groups = {}
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for radio in radios:
                group_name = radio.get_attribute("name") or "unknown"
                if group_name not in radio_groups:
                    radio_groups[group_name] = []
                label_text = ""
                radio_id = radio.get_attribute("id") or ""
                # Try multiple methods to find label
                try:
                    if radio_id:
                        lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                        label_text = lbl.text.strip().lower()
                except:
                    pass
                if not label_text:
                    try:
                        lbl = radio.find_element(By.XPATH, "./ancestor::label")
                        label_text = lbl.text.strip().lower()
                    except:
                        try:
                            lbl = radio.find_element(By.XPATH, "./following-sibling::*[1]")
                            label_text = lbl.text.strip().lower()
                        except:
                            label_text = (radio.get_attribute("value") or "").lower()
                radio_groups[group_name].append((radio, label_text))

            for group_name, group_radios in radio_groups.items():
                # Check if any is already selected (use JS for hidden radios)
                if any(self.driver.execute_script("return arguments[0].checked", r) for r, _ in group_radios):
                    continue
                all_labels = " ".join(label for _, label in group_radios)
                # Get question/heading text from parent card
                question_text = ""
                try:
                    first_radio = group_radios[0][0]
                    card = first_radio.find_element(By.XPATH,
                        "./ancestor::*[contains(@class,'card') or contains(@class,'field') "
                        "or contains(@class,'question') or contains(@class,'application-question')]")
                    headings = card.find_elements(By.CSS_SELECTOR, "label, legend, h3, h4, .text, [class*='label']")
                    if headings:
                        question_text = headings[0].text.strip().lower()
                except:
                    pass
                combined_context = f"{all_labels} {question_text}"

                def click_radio(radio):
                    """Click radio via label or JS"""
                    radio_id = radio.get_attribute("id") or ""
                    try:
                        if radio_id:
                            lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl)
                            time.sleep(0.2)
                            lbl.click()
                            return
                    except:
                        pass
                    try:
                        lbl = radio.find_element(By.XPATH, "./ancestor::label")
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl)
                        time.sleep(0.2)
                        lbl.click()
                        return
                    except:
                        pass
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
                    self.driver.execute_script("arguments[0].click();", radio)

                # Work eligibility (Canada, US, etc)
                if any(w in combined_context for w in ["eligible", "work permit", "visa", "authorized",
                                                         "legally authorized", "right to work"]):
                    for radio, label in group_radios:
                        if any(w in label for w in ["require", "would require", "need", "sponsorship"]):
                            click_radio(radio)
                            logging.info(f"  Lever Radio: Work eligibility = {label[:50]}")
                            break
                    else:
                        # Fallback: if no "require" option, try "yes" (authorized to work)
                        for radio, label in group_radios:
                            if "yes" == label.strip().lower() or label.strip().lower().startswith("yes"):
                                click_radio(radio)
                                logging.info(f"  Lever Radio: Work eligibility (fallback) = Yes")
                                break
                # Pronouns
                elif any(w in combined_context for w in ["he/him", "she/her", "they/them", "pronoun"]):
                    for radio, label in group_radios:
                        if "he/him" in label:
                            click_radio(radio)
                            logging.info("  Lever Radio: Pronouns = He/him")
                            break
                # Gender
                elif any(w in combined_context for w in ["gender", "what is your gender"]):
                    for radio, label in group_radios:
                        if label.strip() == "male" or label.strip().startswith("male"):
                            click_radio(radio)
                            logging.info("  Lever Radio: Gender = Male")
                            break
                # Age range
                elif any(w in combined_context for w in ["age range", "age", "17 or younger", "18-20", "21-29", "30-39"]):
                    for radio, label in group_radios:
                        if "30-39" in label:
                            click_radio(radio)
                            logging.info("  Lever Radio: Age = 30-39")
                            break
                # Yes/No authorization questions
                elif any(w in question_text for w in ["legally authorized", "authorized to work",
                                                        "right to work", "employment visa"]):
                    for radio, label in group_radios:
                        if any(w in label for w in ["require", "need", "sponsorship"]):
                            click_radio(radio)
                            logging.info(f"  Lever Radio: Authorization = {label[:50]}")
                            break
                    else:
                        for radio, label in group_radios:
                            if "yes" == label.strip().lower():
                                click_radio(radio)
                                logging.info(f"  Lever Radio: Authorization = Yes")
                                break
                # Comfortable working hours / timezone availability
                elif any(w in combined_context for w in ["comfortable working", "comfortable with",
                                                           "eet hours", "est hours", "pst hours",
                                                           "cet hours", "gmt hours", "overlap"]):
                    for radio, label in group_radios:
                        if "yes" == label.strip().lower() or label.strip().lower().startswith("yes"):
                            click_radio(radio)
                            logging.info(f"  Lever Radio: Comfortable working = Yes")
                            break
                # Are you 18+ / legal age
                elif any(w in combined_context for w in ["18 years", "18 or older", "over 18", "legal age"]):
                    for radio, label in group_radios:
                        if "yes" == label.strip().lower():
                            click_radio(radio)
                            logging.info("  Lever Radio: 18+ = Yes")
                            break
                # Experience level (years)
                elif any(w in combined_context for w in ["years of experience", "experience level",
                                                           "seniority", "level of experience"]):
                    for radio, label in group_radios:
                        if any(w in label for w in ["5+", "6+", "7+", "8+", "9+", "10+", "senior"]):
                            click_radio(radio)
                            logging.info(f"  Lever Radio: Experience = {label[:30]}")
                            break
                    else:
                        # Select last option (usually highest experience)
                        if group_radios:
                            click_radio(group_radios[-1][0])
                            logging.info(f"  Lever Radio: Experience (last) = {group_radios[-1][1][:30]}")
                # Catch-all: for any Yes/No question, default to "Yes"
                elif len(group_radios) == 2:
                    labels_lower = [l.strip().lower() for _, l in group_radios]
                    if set(labels_lower) == {"yes", "no"} or ("yes" in labels_lower and "no" in labels_lower):
                        for radio, label in group_radios:
                            if "yes" == label.strip().lower():
                                click_radio(radio)
                                logging.info(f"  Lever Radio: Generic Yes/No = Yes ({question_text[:40]})")
                                break
        except Exception as e:
            logging.info(f"  Lever Radio error: {e}")

        # === LEVER: Checkboxes (ethnicity multi-select, consent) ===
        # Note: Lever may hide actual checkboxes, so use JS for checked state and click labels
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for cb in checkboxes:
                label_text = ""
                cb_id = cb.get_attribute("id") or ""
                # Try multiple methods to find label
                try:
                    if cb_id:
                        lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']")
                        label_text = lbl.text.strip().lower()
                except:
                    pass
                if not label_text:
                    try:
                        lbl = cb.find_element(By.XPATH, "./ancestor::label")
                        label_text = lbl.text.strip().lower()
                    except:
                        try:
                            lbl = cb.find_element(By.XPATH, "./following-sibling::*[1]")
                            label_text = lbl.text.strip().lower()
                        except:
                            label_text = (cb.get_attribute("value") or "").lower()
                # Ethnicity: Hispanic/Latino
                if "hispanic" in label_text or "latino" in label_text or "spanish origin" in label_text:
                    is_checked = self.driver.execute_script("return arguments[0].checked", cb)
                    if not is_checked:
                        try:
                            if cb_id:
                                lbl = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{cb_id}']")
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl)
                                time.sleep(0.2)
                                lbl.click()
                            else:
                                self.driver.execute_script("arguments[0].click();", cb)
                        except:
                            self.driver.execute_script("arguments[0].click();", cb)
                        logging.info("  Lever Checkbox: Hispanic/Latino selected")
        except:
            pass

        # === LEVER: Selects (How did you hear, location, etc.) ===
        try:
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            for sel in selects:
                if not sel.is_displayed():
                    continue
                sel_obj = Select(sel)
                current = sel_obj.first_selected_option.text.strip()
                if current and current not in ["Select...", "Select", "-- Select --", "", "Please select"]:
                    continue
                # Get label and parent context
                sel_name = (sel.get_attribute("name") or "").lower()
                label_text = ""
                try:
                    label_text = sel.find_element(By.XPATH, "./preceding::label[1]").text.strip().lower()
                except:
                    pass
                parent_text = ""
                try:
                    card = sel.find_element(By.XPATH,
                        "./ancestor::*[contains(@class,'card') or contains(@class,'field') "
                        "or contains(@class,'question')]")
                    parent_text = card.text.strip()[:200].lower()
                except:
                    pass
                combined = f"{sel_name} {label_text} {parent_text}"
                options = [o.text.strip() for o in sel_obj.options]

                if any(w in combined for w in ["how did you hear", "hear about", "source"]):
                    for opt in options:
                        if any(w in opt.lower() for w in ["online", "internet", "job board",
                                                           "website", "linkedin", "other"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Lever Select: How did you hear = {opt}")
                            break
                # Country select - pick Chile
                elif any(w in combined for w in ["country", "pais", "país"]):
                    for opt in options:
                        if "chile" in opt.lower():
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Lever Select: Country = {opt}")
                            break
                    else:
                        # Try "Other" or first option
                        for opt in options:
                            if any(w in opt.lower() for w in ["other", "international"]):
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Lever Select: Country fallback = {opt}")
                                break
                # State/Province - pick Other/N-A or skip
                elif any(w in combined for w in ["state", "province", "region", "estado"]):
                    for opt in options:
                        if any(w in opt.lower() for w in ["other", "n/a", "outside", "international", "not applicable"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Lever Select: State = {opt}")
                            break
                # Location/Office
                elif any(w in combined for w in ["location", "office", "ubicacion"]):
                    for opt in options:
                        if any(w in opt.lower() for w in ["remote", "other", "international"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Lever Select: Location = {opt}")
                            break
                    else:
                        # If no remote/other option, select first non-placeholder
                        for opt in options:
                            if opt and opt not in ["Select...", "Select", "-- Select --", "", "Please select"]:
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Lever Select: Location fallback = {opt[:30]}")
                                break
                else:
                    # Generic fallback: try "Other" first, then first non-placeholder
                    found = False
                    for opt in options:
                        if any(w in opt.lower() for w in ["other", "n/a", "prefer not"]):
                            sel_obj.select_by_visible_text(opt)
                            logging.info(f"  Lever Select fallback (other): {opt[:30]}")
                            found = True
                            break
                    if not found:
                        for opt in options:
                            if opt and opt not in ["Select...", "Select", "-- Select --", "", "Please select"]:
                                sel_obj.select_by_visible_text(opt)
                                logging.info(f"  Lever Select fallback: {opt[:30]}")
                                break
        except:
            pass

        time.sleep(1)
        return self._hacer_submit()

    def _postular_bamboohr(self, url, carta):
        """Handler para BambooHR ATS"""
        logging.info("  [Plataforma: BambooHR]")
        self.driver.get(url)
        time.sleep(4)

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # BambooHR: buscar botón "Apply for this Job"
        try:
            apply_btn = WebDriverWait(self.driver, 6).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(text(), 'Apply')] | //button[contains(text(), 'Apply')]"
                ))
            )
            apply_btn.click()
            time.sleep(3)
        except:
            logging.info("  Buscando formulario directo en BambooHR...")

        # Llenar formulario
        if self._llenar_campos_comunes(carta):
            time.sleep(1)
            return self._hacer_submit()
        return False

    def _postular_ashby(self, url, carta):
        """Handler para Ashby ATS - Mejorado con soporte completo"""
        logging.info("  [Plataforma: Ashby]")
        self.driver.get(url)
        self._esperar_renderizado_spa(timeout=10)

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # Ashby: buscar botón Apply (multiple strategies)
        apply_found = False
        try:
            apply_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                    "//a[contains(@href, '/application')]"
                ))
            )
            logging.info(f"  Ashby: Botón Apply encontrado: '{apply_btn.text}'")
            apply_btn.click()
            apply_found = True
            self._esperar_renderizado_spa(timeout=10)
        except:
            pass

        # Si no se encontró botón, intentar navegar a /application
        if not apply_found:
            app_url = url.rstrip("/") + "/application"
            logging.info(f"  Ashby: No se encontró botón, intentando {app_url}")
            self.driver.get(app_url)
            self._esperar_renderizado_spa(timeout=10)

        # Verificar expiración post-navegación
        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA (post-apply) - saltando")
            return False

        # Esperar a que el formulario se renderice (React SPA)
        form_found = False
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[type='text'], input[type='email'], input[name*='name'], "
                    "input[name*='email'], form[action], [data-testid]"
                ))
            )
            form_found = True
            logging.info("  Ashby: Formulario detectado")
        except:
            logging.info("  Ashby: No se detectó formulario estándar, intentando igual...")

        # Detectar idioma
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        en_ingles = self._detectar_idioma(page_text) == "EN"

        # Intentar selectores específicos de Ashby primero
        campos_llenados = 0
        ashby_selectors = [
            # Name - Ashby a veces usa un solo campo "Name" o separados
            ([
                "input[name='_systemfield_name']",
                "input[name*='Name' i]:not([name*='last']):not([name*='company'])",
                "input[placeholder*='Full name' i]",
                "input[placeholder*='Your name' i]",
            ], DATOS_PERSONALES["nombre_completo"], "Nombre completo"),
            # First name
            ([
                "input[name*='first' i]",
                "input[placeholder*='First' i]",
                "input[autocomplete='given-name']",
            ], DATOS_PERSONALES["nombre"], "Nombre"),
            # Last name
            ([
                "input[name*='last' i]:not([name*='Name' i])",
                "input[placeholder*='Last' i]",
                "input[autocomplete='family-name']",
            ], DATOS_PERSONALES["apellido"], "Apellido"),
            # Email
            ([
                "input[name='_systemfield_email']",
                "input[type='email']",
                "input[name*='email' i]",
                "input[placeholder*='email' i]",
                "input[autocomplete='email']",
            ], DATOS_PERSONALES["email"], "Email"),
            # Phone
            ([
                "input[name='_systemfield_phone']",
                "input[type='tel']",
                "input[name*='phone' i]",
                "input[placeholder*='phone' i]",
                "input[autocomplete='tel']",
            ], DATOS_PERSONALES["telefono"], "Teléfono"),
            # LinkedIn
            ([
                "input[name*='linkedin' i]",
                "input[placeholder*='linkedin' i]",
                "input[name*='LinkedIn' i]",
            ], DATOS_PERSONALES.get("linkedin", ""), "LinkedIn"),
            # Portfolio/Website
            ([
                "input[name*='portfolio' i]",
                "input[name*='website' i]",
                "input[placeholder*='portfolio' i]",
                "input[placeholder*='website' i]",
            ], DATOS_PERSONALES.get("portfolio", ""), "Portfolio"),
            # Location/City
            ([
                "input[name*='location' i]",
                "input[name*='city' i]",
                "input[placeholder*='location' i]",
                "input[placeholder*='city' i]",
            ], f"{DATOS_PERSONALES['ciudad']}, {DATOS_PERSONALES['pais']}", "Ubicación"),
        ]

        for selectors, valor, nombre in ashby_selectors:
            if not valor:
                continue
            for selector in selectors:
                try:
                    campo = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if campo.is_displayed() and campo.is_enabled():
                        campo.click()
                        time.sleep(0.3)
                        campo.clear()
                        campo.send_keys(valor)
                        logging.info(f"  Ashby: {nombre} llenado ({selector})")
                        campos_llenados += 1
                        break
                except:
                    continue

        # Si Ashby-specific no funcionó, usar análisis inteligente
        if campos_llenados < 2:
            logging.info("  Ashby: Pocos campos específicos, usando análisis inteligente...")
            self._analizar_y_llenar_pagina(carta)
        else:
            # Subir CV
            cv_path = DATOS_PERSONALES["cv_path_en"] if en_ingles else DATOS_PERSONALES["cv_path"]
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_inputs[0].send_keys(cv_path)
                    logging.info("  Ashby: CV subido")
                    time.sleep(2)
                else:
                    # Ashby a veces usa botón de upload con input oculto
                    file_input = self.driver.find_element(By.CSS_SELECTOR,
                        "input[type='file'][style*='display: none'], input[type='file'][hidden], "
                        "input[type='file'][accept*='pdf']")
                    file_input.send_keys(cv_path)
                    logging.info("  Ashby: CV subido (input oculto)")
                    time.sleep(2)
            except:
                logging.info("  Ashby: No se encontró input de CV")

            # Carta de presentación
            try:
                textareas = self.driver.find_elements(By.CSS_SELECTOR, "textarea")
                for ta in textareas:
                    try:
                        if ta.is_displayed():
                            # Verificar si es un campo de cover letter
                            ta_name = ta.get_attribute("name") or ""
                            ta_placeholder = ta.get_attribute("placeholder") or ""
                            ta_label = ""
                            try:
                                ta_id = ta.get_attribute("id")
                                if ta_id:
                                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{ta_id}']")
                                    ta_label = label.text.lower()
                            except:
                                pass
                            context = f"{ta_name} {ta_placeholder} {ta_label}".lower()
                            if any(kw in context for kw in ["cover", "carta", "letter", "why", "interest", "about"]):
                                ta.click()
                                ta.clear()
                                ta.send_keys(carta[:3000])
                                logging.info("  Ashby: Carta de presentación escrita")
                                break
                            elif not any(kw in context for kw in ["address", "street", "referral"]):
                                # Si es el único textarea visible, probablemente es la carta
                                ta.click()
                                ta.clear()
                                ta.send_keys(carta[:3000])
                                logging.info("  Ashby: Textarea llenado (posible carta)")
                                break
                    except:
                        continue
            except:
                pass

        # Ashby: manejar preguntas custom con radio/select
        try:
            selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
            for sel in selects:
                try:
                    if sel.is_displayed():
                        sel_name = (sel.get_attribute("name") or "").lower()
                        from selenium.webdriver.support.ui import Select
                        select_obj = Select(sel)
                        options = [o.text.lower() for o in select_obj.options]
                        # Buscar opciones relevantes
                        if any("yes" in o for o in options):
                            for opt in select_obj.options:
                                if "yes" in opt.text.lower():
                                    select_obj.select_by_visible_text(opt.text)
                                    logging.info(f"  Ashby: Select '{sel_name}' -> '{opt.text}'")
                                    break
                except:
                    continue
        except:
            pass

        time.sleep(1)
        return self._hacer_submit()

    def _postular_workable(self, url, carta):
        """Handler para Workable ATS (React SPA - necesita espera extra)"""
        logging.info("  [Plataforma: Workable]")

        # Primero cargar la página de la oferta (no /apply directo)
        self.driver.get(url.rstrip("/"))
        # Espera inteligente en vez de sleep fijo
        self._esperar_renderizado_spa(timeout=12)

        # Cerrar cookie banners
        self._cerrar_cookie_banners()

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # Verificar expiración de nuevo después del renderizado
        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA (post-render) - saltando")
            return False

        # Buscar botón Apply en la página de la oferta
        try:
            apply_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')]"
                ))
            )
            logging.info(f"  Workable: Botón Apply encontrado: '{apply_btn.text}'")
            apply_btn.click()
            self._esperar_renderizado_spa(timeout=10)
        except:
            # Ir directo a /apply
            apply_url = url.rstrip("/") + "/apply"
            logging.info(f"  Workable: No se encontró botón, intentando {apply_url}")
            self.driver.get(apply_url)
            self._esperar_renderizado_spa(timeout=12)

        # Esperar renderizado del formulario
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[type='text'], input[type='email'], input[name='firstname'], "
                    "input[name='lastname'], input[data-ui='input']"
                ))
            )
            logging.info("  Workable: Formulario detectado")
        except:
            logging.info("  Workable: No se encontró formulario")

        # Detectar idioma
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        en_ingles = self._detectar_idioma(page_text) == "EN"

        # Intentar llenar campos específicos de Workable con _find_first_match
        campos_workable = [
            (["input[name='firstname']", "input[data-ui='input'][autocomplete='given-name']",
              "input[autocomplete='given-name']", "input[placeholder*='First']"],
             DATOS_PERSONALES["nombre"], "Nombre"),
            (["input[name='lastname']", "input[data-ui='input'][autocomplete='family-name']",
              "input[autocomplete='family-name']", "input[placeholder*='Last']"],
             DATOS_PERSONALES["apellido"], "Apellido"),
            (["input[name='email']", "input[type='email']", "input[autocomplete='email']"],
             DATOS_PERSONALES["email"], "Email"),
            (["input[name='phone']", "input[type='tel']", "input[autocomplete='tel']"],
             DATOS_PERSONALES["telefono"], "Teléfono"),
        ]

        campos_llenados = 0
        for selectors, valor, nombre in campos_workable:
            campo = self._find_first_match(selectors)
            if campo:
                try:
                    campo.click()
                    time.sleep(0.3)
                    campo.clear()
                    campo.send_keys(valor)
                    logging.info(f"  Workable: {nombre} llenado")
                    campos_llenados += 1
                except:
                    pass

        # Si no se llenaron campos de Workable, usar análisis inteligente
        if campos_llenados == 0:
            logging.info("  Workable: Selectores específicos fallaron, usando análisis inteligente...")
            if self._analizar_y_llenar_pagina(carta):
                time.sleep(1)
                return self._hacer_submit()
            # Último intento: llenar campos comunes
            logging.info("  Workable: Análisis inteligente falló, intentando campos comunes...")
            if self._llenar_campos_comunes(carta):
                time.sleep(1)
                return self._hacer_submit()
            return False

        # Subir CV
        cv_path = DATOS_PERSONALES["cv_path_en"] if en_ingles else DATOS_PERSONALES["cv_path"]
        try:
            resume_input = self.driver.find_element(By.CSS_SELECTOR,
                "input[type='file'][accept*='pdf'], input[type='file']")
            resume_input.send_keys(cv_path)
            logging.info(f"  Workable: CV subido")
            time.sleep(2)
        except:
            logging.info("  Workable: No se encontró input de CV")

        # Carta de presentación (textarea)
        try:
            textarea = self.driver.find_element(By.CSS_SELECTOR,
                "textarea[name='cover_letter'], textarea[data-ui='textarea'], textarea")
            if textarea.is_displayed():
                textarea.click()
                textarea.clear()
                textarea.send_keys(carta[:2000])
                logging.info("  Workable: Carta escrita")
        except:
            pass

        time.sleep(1)
        return self._hacer_submit()

    def _postular_smartrecruiters(self, url, carta):
        """Handler para SmartRecruiters ATS"""
        logging.info("  [Plataforma: SmartRecruiters]")
        self.driver.get(url)
        time.sleep(4)

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # Buscar botón Apply
        try:
            apply_btn = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')]"
                ))
            )
            logging.info(f"  SmartRecruiters: Botón Apply encontrado: '{apply_btn.text}'")
            apply_btn.click()
            time.sleep(4)
        except:
            logging.info("  SmartRecruiters: No se encontró botón Apply")

        # Detectar idioma
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        en_ingles = self._detectar_idioma(page_text) == "EN"

        # SmartRecruiters campos comunes con _find_first_match
        campos_sr = [
            (["input[name='firstName']", "input#firstName", "input[aria-label*='First']",
              "input[autocomplete='given-name']", "input[placeholder*='First']"],
             DATOS_PERSONALES["nombre"], "Nombre"),
            (["input[name='lastName']", "input#lastName", "input[aria-label*='Last']",
              "input[autocomplete='family-name']", "input[placeholder*='Last']"],
             DATOS_PERSONALES["apellido"], "Apellido"),
            (["input[name='email']", "input#email", "input[type='email']",
              "input[autocomplete='email']"],
             DATOS_PERSONALES["email"], "Email"),
            (["input[name='phoneNumber']", "input#phone", "input[type='tel']",
              "input[autocomplete='tel']"],
             DATOS_PERSONALES["telefono"], "Teléfono"),
        ]

        campos_llenados = 0
        for selectors, valor, nombre in campos_sr:
            campo = self._find_first_match(selectors)
            if campo:
                try:
                    campo.click()
                    time.sleep(0.3)
                    campo.clear()
                    campo.send_keys(valor)
                    logging.info(f"  SmartRecruiters: {nombre} llenado")
                    campos_llenados += 1
                except:
                    pass

        if campos_llenados == 0:
            # Intentar con handler genérico
            if self._llenar_campos_comunes(carta):
                time.sleep(1)
                return self._hacer_submit()
            # Segundo fallback: análisis inteligente
            logging.info("  SmartRecruiters: Intentando análisis inteligente...")
            if self._analizar_y_llenar_pagina(carta):
                time.sleep(1)
                return self._hacer_submit()
            return False

        # Subir CV
        cv_path = DATOS_PERSONALES["cv_path_en"] if en_ingles else DATOS_PERSONALES["cv_path"]
        try:
            resume_input = self.driver.find_element(By.CSS_SELECTOR,
                "input[type='file']")
            resume_input.send_keys(cv_path)
            logging.info(f"  SmartRecruiters: CV subido")
            time.sleep(2)
        except:
            logging.info("  SmartRecruiters: No se encontró input de CV")

        # Carta de presentación
        try:
            textarea = self.driver.find_element(By.CSS_SELECTOR,
                "textarea[name='coverLetter'], textarea")
            if textarea.is_displayed():
                textarea.click()
                textarea.clear()
                textarea.send_keys(carta[:2000])
                logging.info("  SmartRecruiters: Carta escrita")
        except:
            pass

        time.sleep(1)
        return self._hacer_submit()

    def _postular_generic_ats(self, url, carta):
        """Handler genérico para ATS con formulario directo"""
        logging.info("  [Plataforma: Formulario directo]")
        self.driver.get(url)
        time.sleep(3)

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        if self._llenar_campos_comunes(carta):
            time.sleep(1)
            return self._hacer_submit()
        return False

    def _postular_linkedin(self, url, carta):
        """Handler para LinkedIn (usa sesión de Google del perfil Edge)"""
        logging.info("  [Plataforma: LinkedIn]")
        self.driver.get(url)
        time.sleep(4)

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # Si hay modal de login, intentar cerrarla primero
        try:
            modal_close = self.driver.find_elements(By.CSS_SELECTOR,
                "button[aria-label='Dismiss'], button.modal__dismiss, "
                "button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']")
            for btn in modal_close:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    break
        except:
            pass

        # Intentar clic en botón "Apply" / "Solicitar" / "Easy Apply"
        try:
            apply_btn = WebDriverWait(self.driver, 6).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(text(), 'Apply')] | //a[contains(text(), 'Apply')] | "
                    "//button[contains(text(), 'Solicitar')] | //a[contains(text(), 'Solicitar')]"
                ))
            )
            self.driver.execute_script("arguments[0].click();", apply_btn)
            time.sleep(3)
            self._manejar_nueva_ventana()
        except:
            logging.info("  No se pudo hacer clic en Apply de LinkedIn")
            return False

        # Si se abrió un formulario, intentar llenarlo
        if self._llenar_campos_comunes(carta):
            time.sleep(1)
            return self._hacer_submit()
        return False

    def _postular_con_login(self, url, carta):
        """Handler para sitios que requieren login (Globant, GetOnBrd, etc.)"""
        logging.info("  [Plataforma: Sitio con login - usando sesión Google]")
        self.driver.get(url)
        time.sleep(4)

        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False

        # Buscar botón de Apply/Postular
        try:
            apply_btn = WebDriverWait(self.driver, 6).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'postular')] | "
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'postular')]"
                ))
            )
            apply_btn.click()
            time.sleep(3)
            self._manejar_nueva_ventana()
        except:
            logging.info("  No se encontró botón de aplicación")

        # Si aparece opción de Google Sign-In, intentar usarla
        try:
            google_btn = self.driver.find_elements(By.XPATH,
                "//a[contains(@href, 'google')] | //button[contains(text(), 'Google')] | "
                "//a[contains(text(), 'Google')] | //button[contains(@class, 'google')]")
            for btn in google_btn:
                if btn.is_displayed():
                    logging.info("  Botón Google Sign-In encontrado, haciendo clic...")
                    btn.click()
                    time.sleep(5)
                    self._manejar_nueva_ventana()
                    # Seleccionar cuenta de Google si aparece
                    try:
                        email_div = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH,
                                f"//div[contains(text(), '{DATOS_PERSONALES['email']}')]"
                            ))
                        )
                        email_div.click()
                        time.sleep(5)
                        logging.info("  Cuenta de Google seleccionada")
                    except:
                        logging.info("  No se encontró selector de cuenta Google")
                    break
        except:
            pass

        # Intentar llenar formulario
        if self._llenar_campos_comunes(carta):
            time.sleep(1)
            return self._hacer_submit()
        return False

    def _intentar_aplicar_directo(self, carta):
        """Intenta encontrar y completar formulario de aplicación (handler genérico)"""
        if self._pagina_expirada(url):
            logging.info("  OFERTA EXPIRADA - saltando")
            return False
        try:
            # Buscar botones de aplicación comunes
            botones_apply = [
                "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'postular')]",
                "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'postular')]",
                "//a[contains(@class, 'apply')]",
                "//button[contains(@class, 'apply')]",
                "//a[contains(@href, 'apply')]",
                "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'solicitar')]",
            ]

            boton = None
            for xpath in botones_apply:
                try:
                    elementos = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elementos:
                        if elem.is_displayed():
                            boton = elem
                            break
                    if boton:
                        break
                except:
                    continue

            if boton:
                logging.info("  Botón de aplicación encontrado, haciendo clic...")
                boton.click()
                time.sleep(3)
                self._manejar_nueva_ventana()

            # Primero intentar análisis inteligente de página
            if self._analizar_y_llenar_pagina(carta):
                time.sleep(1)
                return self._hacer_submit()

            # Fallback a campos comunes si el análisis inteligente no funcionó
            if self._llenar_campos_comunes(carta):
                time.sleep(1)
                return self._hacer_submit()

            return False

        except Exception as e:
            logging.warning(f"  No se pudo aplicar directamente: {e}")
            return False

    def _guardar_postulacion_pendiente(self, oferta, carta):
        """Guarda la info de postulación pendiente para revisión manual"""
        pendientes_dir = os.path.join(WORK_DIR, "postulaciones_pendientes")
        os.makedirs(pendientes_dir, exist_ok=True)

        nombre_archivo = re.sub(r'[^\w\s-]', '', f"{oferta['empresa']}_{oferta['titulo']}")[:60]
        filepath = os.path.join(pendientes_dir, f"{nombre_archivo}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"POSTULACIÓN PENDIENTE\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Empresa: {oferta['empresa']}\n")
            f.write(f"Puesto: {oferta['titulo']}\n")
            f.write(f"Ubicación: {oferta['ubicacion']}\n")
            f.write(f"Salario: {oferta['salario']}\n")
            f.write(f"URL: {oferta['url']}\n")
            f.write(f"Fuente: {oferta['fuente']}\n\n")
            f.write(f"CARTA DE PRESENTACIÓN:\n")
            f.write(f"{'-'*50}\n")
            f.write(carta)
            f.write(f"\n\n{'='*50}\n")
            f.write(f"INSTRUCCIONES:\n")
            f.write(f"1. Abre la URL en tu navegador\n")
            f.write(f"2. Busca el botón de 'Apply' o 'Postular'\n")
            f.write(f"3. Llena tus datos y pega la carta de arriba\n")
            f.write(f"4. Sube tu CV: {DATOS_PERSONALES['cv_path']}\n")


# ============================================================
# GENERADOR DE REPORTE HTML
# ============================================================
def generar_reporte(ofertas, exitosas, fallidas):
    """Genera un reporte HTML bonito con los resultados"""

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Postulaciones - {fecha}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 30px; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{ color: #00b4d8; margin-bottom: 5px; font-size: 28px; }}
        .subtitle {{ color: #888; margin-bottom: 25px; font-size: 14px; }}
        .stats {{ display: flex; gap: 15px; margin-bottom: 25px; }}
        .stat-card {{ background: #16213e; padding: 20px; border-radius: 10px; flex: 1; text-align: center; }}
        .stat-number {{ font-size: 36px; font-weight: 800; }}
        .stat-number.blue {{ color: #00b4d8; }}
        .stat-number.green {{ color: #00c853; }}
        .stat-number.orange {{ color: #ff9800; }}
        .stat-label {{ font-size: 12px; color: #999; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        th {{ background: #16213e; color: #00b4d8; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #2a2a4a; font-size: 13px; }}
        tr:hover {{ background: #16213e; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
        .badge-success {{ background: #00c85333; color: #00c853; }}
        .badge-pending {{ background: #ff980033; color: #ff9800; }}
        .badge-source {{ background: #00b4d833; color: #00b4d8; }}
        a {{ color: #00b4d8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .section-title {{ color: #00b4d8; font-size: 18px; margin: 25px 0 15px; padding-bottom: 8px; border-bottom: 1px solid #2a2a4a; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte de Auto-Postulación</h1>
        <div class="subtitle">{fecha} — {DATOS_PERSONALES["nombre_completo"]}</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number blue">{len(ofertas)}</div>
                <div class="stat-label">Ofertas Encontradas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number green">{len(exitosas)}</div>
                <div class="stat-label">Postulaciones Exitosas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number orange">{len(fallidas)}</div>
                <div class="stat-label">Pendientes (Manual)</div>
            </div>
        </div>

        <div class="section-title">Postulaciones Realizadas</div>
        <table>
            <tr>
                <th>Puesto</th>
                <th>Empresa</th>
                <th>Ubicación</th>
                <th>Fuente</th>
                <th>Estado</th>
                <th>Link</th>
            </tr>"""

    for oferta in exitosas:
        html += f"""
            <tr>
                <td>{oferta['titulo']}</td>
                <td>{oferta['empresa']}</td>
                <td>{oferta['ubicacion']}</td>
                <td><span class="badge badge-source">{oferta['fuente']}</span></td>
                <td><span class="badge badge-success">APLICADO</span></td>
                <td><a href="{oferta['url']}" target="_blank">Ver oferta</a></td>
            </tr>"""

    for oferta in fallidas:
        html += f"""
            <tr>
                <td>{oferta['titulo']}</td>
                <td>{oferta['empresa']}</td>
                <td>{oferta['ubicacion']}</td>
                <td><span class="badge badge-source">{oferta['fuente']}</span></td>
                <td><span class="badge badge-pending">PENDIENTE</span></td>
                <td><a href="{oferta['url']}" target="_blank">Aplicar manual</a></td>
            </tr>"""

    html += """
        </table>

        <div class="section-title">Todas las Ofertas Encontradas</div>
        <table>
            <tr>
                <th>Puesto</th>
                <th>Empresa</th>
                <th>Ubicación</th>
                <th>Salario</th>
                <th>Fuente</th>
                <th>Link</th>
            </tr>"""

    for oferta in ofertas:
        html += f"""
            <tr>
                <td>{oferta['titulo']}</td>
                <td>{oferta['empresa']}</td>
                <td>{oferta['ubicacion']}</td>
                <td>{oferta['salario']}</td>
                <td><span class="badge badge-source">{oferta['fuente']}</span></td>
                <td><a href="{oferta['url']}" target="_blank">Ver</a></td>
            </tr>"""

    html += """
        </table>
    </div>
</body>
</html>"""

    return html


# ============================================================
# ENVIAR EMAIL CON RESULTADOS
# ============================================================
def enviar_email(asunto, html_content):
    """Envía un email con los resultados"""
    if not GMAIL_APP_PASSWORD:
        logging.warning("No se configuró contraseña de Gmail. Email no enviado.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())

        logging.info("Email enviado exitosamente!")
        return True
    except Exception as e:
        logging.error(f"Error enviando email: {e}")
        return False


# ============================================================
# REGISTRO DE URLs APLICADAS (persistente entre runs)
# ============================================================
URLS_APLICADAS_FILE = os.path.join(WORK_DIR, "urls_aplicadas.txt")
URLS_EXPIRADAS_FILE = os.path.join(WORK_DIR, "urls_expiradas.txt")

def _cargar_urls_desde_archivo(filepath):
    """Carga URLs desde un archivo de texto (una por línea, ignora comentarios #)"""
    urls = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.add(line)
    return urls

def cargar_urls_aplicadas():
    """Carga URLs ya aplicadas desde archivo persistente"""
    return _cargar_urls_desde_archivo(URLS_APLICADAS_FILE)

def cargar_urls_expiradas():
    """Carga URLs expiradas/404 desde archivo persistente"""
    return _cargar_urls_desde_archivo(URLS_EXPIRADAS_FILE)

def guardar_url_aplicada(url):
    """Guarda una URL exitosa al archivo inmediatamente"""
    with open(URLS_APLICADAS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")

def guardar_url_expirada(url):
    """Guarda una URL expirada/404 al archivo para no volver a intentarla"""
    with open(URLS_EXPIRADAS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================
def main():
    # Configurar logging
    log_file = os.path.join(WORK_DIR, "auto_postulador.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logging.info("=" * 60)
    logging.info("  AUTO-POSTULADOR DE TRABAJOS INICIADO")
    logging.info(f"  Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    logging.info("=" * 60)

    # Cerrar Edge existente para poder usar el perfil
    logging.info("Cerrando Edge existente para usar perfil de usuario...")
    try:
        import subprocess
        subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True)
        time.sleep(2)
    except:
        pass

    # PASO 1: Buscar ofertas + agregar ofertas conocidas
    logging.info("\n[PASO 1/4] Buscando ofertas de trabajo...")
    buscador = BuscadorOfertas()
    ofertas = buscador.buscar_todas()

    # Agregar ofertas conocidas (URLs guardadas manualmente)
    logging.info(f"\nAgregando {len(OFERTAS_CONOCIDAS)} ofertas conocidas...")
    vistos_urls = {o.get('url', '') for o in ofertas}
    for oferta_conocida in OFERTAS_CONOCIDAS:
        if oferta_conocida.get('url', '') not in vistos_urls:
            ofertas.append(oferta_conocida)
            vistos_urls.add(oferta_conocida.get('url', ''))

    logging.info(f"Total ofertas a procesar: {len(ofertas)}")

    if not ofertas:
        logging.warning("No se encontraron ofertas. Intentar más tarde.")
        return

    # Cargar URLs aplicadas y expiradas desde archivos persistentes
    urls_aplicadas_file = cargar_urls_aplicadas()
    urls_expiradas_file = cargar_urls_expiradas()
    logging.info(f"  URLs ya aplicadas (archivo): {len(urls_aplicadas_file)}")
    logging.info(f"  URLs expiradas (archivo): {len(urls_expiradas_file)}")

    # Filtrar ofertas ya aplicadas O expiradas
    ofertas_filtradas = []
    for oferta in ofertas:
        url = oferta.get("url", "")
        ya_aplicada_hardcoded = any(ya in url for ya in URLS_YA_APLICADAS)
        ya_aplicada_archivo = url in urls_aplicadas_file
        ya_expirada = url in urls_expiradas_file
        if ya_aplicada_hardcoded or ya_aplicada_archivo:
            logging.info(f"  SALTANDO (ya aplicado): {oferta['titulo']} en {oferta['empresa']}")
        elif ya_expirada:
            logging.info(f"  SALTANDO (expirada/404): {oferta['titulo']} en {oferta['empresa']}")
        else:
            ofertas_filtradas.append(oferta)
    ofertas = ofertas_filtradas

    # Filtrar ofertas no relevantes (Java, React, Full Stack sin UE)
    def es_relevante_ue(oferta):
        titulo = oferta.get("titulo", "").lower()
        desc = oferta.get("descripcion", "").lower()
        texto = f"{titulo} {desc}"
        # Si el título explícitamente menciona UE/game, es relevante
        if any(kw in texto for kw in ["unreal", "ue5", "ue4", "game dev", "gameplay",
                                       "game prog", "level design", "technical artist",
                                       "environment artist", "game design", "blueprint",
                                       "videojuego", "ocean"]):
            return True
        # Si no menciona UE y es Java/React/Full Stack, filtrar
        if any(kw in titulo for kw in ["java", "react", "full stack", "fullstack",
                                        "angular", "vue", "ruby", "django", "php"]):
            return False
        return True  # Por defecto incluir

    antes = len(ofertas)
    ofertas = [o for o in ofertas if es_relevante_ue(o)]
    if antes != len(ofertas):
        logging.info(f"  Filtradas {antes - len(ofertas)} ofertas no relevantes a UE")
    logging.info(f"  Ofertas relevantes a procesar: {len(ofertas)}")

    # PASO 2: Auto-postular
    logging.info(f"\n[PASO 2/4] Postulando automáticamente a {len(ofertas)} ofertas...")
    postulador = AutoPostulador(headless=False, usar_perfil=True)  # Con perfil de usuario + Google

    urls_aplicadas_run = set()  # URLs aplicadas durante este run

    try:
        postulador.iniciar_navegador()

        for i, oferta in enumerate(ofertas, 1):
            url = oferta.get("url", "")
            # Saltar si ya se aplicó durante este mismo run
            if url in urls_aplicadas_run:
                logging.info(f"\n--- Oferta {i}/{len(ofertas)} --- SALTANDO (ya aplicado en este run)")
                continue

            logging.info(f"\n--- Oferta {i}/{len(ofertas)} ---")

            try:
                exito = postulador.postular_a_oferta(oferta)
            except Exception as e:
                error_msg = str(e)
                if "invalid session id" in error_msg or "session deleted" in error_msg or "not connected to DevTools" in error_msg:
                    logging.warning(f"  BROWSER CRASH detectado en oferta {i}. Reiniciando navegador...")
                    try:
                        postulador.cerrar_navegador()
                    except Exception:
                        pass
                    time.sleep(3)
                    postulador.iniciar_navegador()
                    logging.info(f"  Navegador reiniciado. Reintentando oferta {i}...")
                    try:
                        exito = postulador.postular_a_oferta(oferta)
                    except Exception as e2:
                        logging.error(f"  Fallo tras reinicio: {e2}")
                        exito = False
                else:
                    logging.error(f"  Error inesperado: {e}")
                    exito = False

            if exito:
                # Guardar URL inmediatamente al archivo persistente
                guardar_url_aplicada(url)
                urls_aplicadas_run.add(url)
                logging.info(f"  URL guardada en registro de aplicadas")

            time.sleep(2)  # Pausa entre postulaciones

    finally:
        postulador.cerrar_navegador()

    # PASO 3: Generar reporte
    logging.info("\n[PASO 3/4] Generando reporte...")
    reporte_html = generar_reporte(
        ofertas,
        postulador.postulaciones_exitosas,
        postulador.postulaciones_fallidas
    )

    reporte_path = os.path.join(WORK_DIR, "reporte_postulaciones.html")
    with open(reporte_path, "w", encoding="utf-8") as f:
        f.write(reporte_html)
    logging.info(f"Reporte guardado: {reporte_path}")

    # Abrir reporte en navegador
    os.startfile(reporte_path)

    # PASO 4: Enviar email
    logging.info("\n[PASO 4/4] Enviando resultados por email...")
    fecha = datetime.now().strftime("%d/%m/%Y")
    asunto = f"[Auto-Postulador] Reporte {fecha}: {len(postulador.postulaciones_exitosas)} aplicadas, {len(postulador.postulaciones_fallidas)} pendientes"
    enviar_email(asunto, reporte_html)

    # Resumen final
    logging.info("\n" + "=" * 60)
    logging.info("  RESUMEN FINAL")
    logging.info("=" * 60)
    logging.info(f"  Ofertas encontradas:       {len(ofertas)}")
    logging.info(f"  Postulaciones exitosas:    {len(postulador.postulaciones_exitosas)}")
    logging.info(f"  Postulaciones pendientes:  {len(postulador.postulaciones_fallidas)}")
    logging.info(f"  Reporte: {reporte_path}")
    logging.info(f"  Log: {log_file}")

    if postulador.postulaciones_fallidas:
        logging.info(f"\n  Las postulaciones pendientes están en:")
        logging.info(f"  {os.path.join(WORK_DIR, 'postulaciones_pendientes')}")
        logging.info(f"  Cada archivo tiene la carta de presentación lista para copiar y pegar.")

    logging.info("\n  ¡Listo! Buena suerte con las postulaciones.")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
