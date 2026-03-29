"""
Dados de seed para demonstração do MVP Carbon Verify.
200 projetos: 100 Verra (VCS) + 100 Gold Standard (GS).
Distribuição de qualidade:
  - 60% (120) projetos bons (score > 60)
  - 30% (60) projetos medianos / atenção (score 40-60)
  - 10% (20) projetos ruins / rejeição (score < 40)
"""
from datetime import datetime, timezone
import random

random.seed(42)

# ─── Dados auxiliares ──────────────────────────────────────────────────

VERRA_METHODOLOGIES = {
    "REDD+": ["VM0004", "VM0006", "VM0007", "VM0009", "VM0015"],
    "ARR": ["AR-ACM0003", "VM0010", "AR-AM0014"],
    "Renewable Energy": ["ACM0002", "ACM0018", "AMS-I.D"],
    "Cookstove": ["VMR0006", "AMS-II.G", "AMS-I.E"],
    "Methane Avoidance": ["AMS-III.D", "AMS-III.H", "ACM0010"],
    "Blue Carbon": ["VM0033", "VM0007", "AR-AM0014"],
    "Biochar": ["VM0044", "Puro Standard"],
    "Other": ["AMS-III.H", "AMS-III.BF"],
}

GS_METHODOLOGIES = {
    "REDD+": ["GS-REDD-001", "GS-AFOLU-001"],
    "ARR": ["GS-AR-001", "GS-AFOLU-002", "AR-ACM0003"],
    "Renewable Energy": ["GS-RE-001", "GS-RE-002", "AMS-I.D"],
    "Cookstove": ["TPDDTEC", "GS-COOK-001", "AMS-II.G"],
    "Methane Avoidance": ["GS-METH-001", "AMS-III.D"],
    "Blue Carbon": ["GS-BC-001", "GS-AFOLU-003"],
    "Biochar": ["GS-BIOCHAR-001"],
    "Other": ["GS-WASH-001", "GS-WASTE-001"],
}

COUNTRIES = [
    ("Brazil", "Pará", -3.5, -50.5), ("Brazil", "Amazonas", -3.1, -60.0),
    ("Brazil", "Mato Grosso", -12.6, -55.4), ("Brazil", "Bahia", -12.9, -38.5),
    ("Brazil", "Minas Gerais", -19.9, -43.9),
    ("Indonesia", "Central Kalimantan", -2.85, 112.15), ("Indonesia", "West Papua", -1.5, 134.0),
    ("Indonesia", "Sumatra", 0.5, 101.5), ("Indonesia", "Java", -7.6, 110.4),
    ("Peru", "Ucayali", -8.4, -74.5), ("Peru", "Madre de Dios", -12.6, -69.2),
    ("Colombia", "Chocó", 5.7, -76.6), ("Colombia", "Amazonas", -1.0, -71.9),
    ("Colombia", "Antioquia", 6.2, -75.6), ("Colombia", "Nariño", 1.8, -78.75),
    ("India", "Gujarat", 23.2, 72.7), ("India", "Rajasthan", 26.9, 75.8),
    ("India", "Tamil Nadu", 11.1, 78.7), ("India", "Maharashtra", 19.1, 72.9),
    ("India", "Karnataka", 15.3, 75.7), ("India", "Uttar Pradesh", 26.8, 80.9),
    ("Kenya", "Rift Valley", -0.5, 36.1), ("Kenya", "Coastal", -4.0, 39.7),
    ("Kenya", "Nairobi", -1.3, 36.8),
    ("Cambodia", "Prey Lang", 13.1, 105.5), ("Cambodia", "Mondulkiri", 12.5, 107.2),
    ("Vietnam", "Dong Nai", 10.95, 106.85), ("Vietnam", "Lam Dong", 11.9, 108.4),
    ("Vietnam", "Hanoi", 21.0, 105.8),
    ("Congo", "Mai-Ndombe", -2.1, 18.3), ("Tanzania", "Kilosa", -6.8, 37.0),
    ("Mozambique", "Sofala", -19.8, 34.9), ("Mexico", "Chiapas", 16.8, -92.6),
    ("Guatemala", "Petén", 16.9, -89.9), ("Myanmar", "Tanintharyi", 12.1, 99.0),
    ("Philippines", "Palawan", 9.5, 118.7), ("Philippines", "Luzon", 14.6, 121.0),
    ("Madagascar", "Analanjirofo", -15.7, 49.6), ("Ethiopia", "Amhara", 11.6, 37.4),
    ("Bangladesh", "Khulna", 22.8, 89.55), ("Bangladesh", "Dhaka", 23.8, 90.4),
    ("United States", "Oregon", 44.0, -120.5), ("China", "Yunnan", 25.0, 102.7),
    ("China", "Sichuan", 30.6, 104.1),
    ("Thailand", "Chiang Mai", 18.8, 98.9), ("Thailand", "Bangkok", 13.8, 100.5),
    ("Nepal", "Terai", 27.7, 85.3), ("Nepal", "Bagmati", 27.7, 85.3),
    ("Papua New Guinea", "Western", -6.0, 141.0), ("Guyana", "Barima-Waini", 7.5, -59.8),
    ("Uganda", "Western", 0.3, 30.5), ("Uganda", "Northern", 2.8, 32.3),
    ("Rwanda", "Eastern", -1.9, 30.1), ("Ghana", "Ashanti", 6.7, -1.6),
    ("Ghana", "Northern", 9.4, -0.8), ("Malawi", "Central", -13.9, 33.8),
    ("Zambia", "Copperbelt", -12.8, 28.2), ("Senegal", "Dakar", 14.7, -17.4),
    ("Mali", "Bamako", 12.6, -8.0), ("Burkina Faso", "Centre", 12.4, -1.5),
    ("Honduras", "Francisco Morazán", 14.1, -87.2), ("Nicaragua", "Managua", 12.1, -86.3),
    ("Turkey", "Ankara", 39.9, 32.9), ("Morocco", "Rabat", 34.0, -6.8),
    ("South Africa", "Western Cape", -33.9, 18.4),
]

PROJECT_TYPES = ["REDD+", "ARR", "Renewable Energy", "Cookstove", "Methane Avoidance", "Blue Carbon", "Biochar", "Other"]

PROPONENTS_VERRA = [
    "InfiniteEARTH", "Biofilica", "Wildlife Works", "South Pole", "Pachama",
    "Verra Climate Solutions", "EcoAct", "Natural Capital Partners", "3Degrees",
    "ClimatePartner", "Terrapass", "Carbon Credit Capital", "Everland",
    "Conservation International", "TerraCarbon", "Forest Carbon", "Carbonext",
    "Adani Green Energy", "Suzlon Energy", "ReNew Power", "Azure Power",
    "Pacific Biochar", "CarbonCure", "Climeworks", "Running Tide",
]

PROPONENTS_GS = [
    "Climate PAL", "Impact Carbon", "UpEnergy", "Burn Manufacturing",
    "Gold Standard Foundation", "myclimate", "atmosfair", "Nexus Carbon",
    "C-Quest Capital", "DelAgua Health", "BioLite", "Envirofit",
    "Solar Sister", "M-KOPA", "d.light", "Greenlight Planet",
    "Husk Power Systems", "SunCulture", "EarthEnable", "Sanergy",
    "Water.org", "Evidence Action", "Living Goods", "One Acre Fund",
]

MONITORING_FREQUENCIES = ["Annual", "Biannual", "Quarterly"]

# ─── Quality tier definitions ─────────────────────────────────────────
# GOOD (60%): full documentation, proper buffer, recent vintage, good methodology
# MEDIUM (30%): partial docs, lower buffer, older vintage, some gaps
# BAD (10%): missing docs, no buffer, very old vintage, governance gaps


def _gen_description(name, ptype, country, area, registry):
    prefix = "Gold Standard" if registry == "Gold Standard" else ""
    descs = {
        "REDD+": f"Projeto {prefix} de conservação florestal {name} em {country}, protegendo {area:,.0f} hectares de floresta nativa contra desmatamento.",
        "ARR": f"Projeto {prefix} de reflorestamento {name} em {country}, restaurando {area:,.0f} hectares de terras degradadas com espécies nativas.",
        "Renewable Energy": f"Projeto {prefix} de energia renovável {name} em {country}, gerando eletricidade limpa e substituindo fontes fósseis.",
        "Cookstove": f"Programa {prefix} de fogões eficientes {name} em {country}, reduzindo consumo de biomassa e emissões de GEE.",
        "Methane Avoidance": f"Projeto {prefix} de captura de metano {name} em {country}, evitando emissões de CH4 de fontes orgânicas.",
        "Blue Carbon": f"Projeto {prefix} de carbono azul {name} em {country}, restaurando {area:,.0f} hectares de ecossistemas costeiros.",
        "Biochar": f"Projeto {prefix} de biochar {name} em {country}, convertendo resíduos em carvão estável para sequestro de carbono.",
        "Other": f"Projeto {prefix} de mitigação climática {name} em {country}, implementando soluções inovadoras para redução de emissões.",
    }
    return descs.get(ptype, descs["Other"])


# ─── Project name templates ───────────────────────────────────────────

_GOOD_NAMES_VERRA = [
    ("Rimba Raya Biodiversity Reserve", "REDD+"), ("Pacajai Amazon Conservation", "REDD+"),
    ("Maísa Forest Protection", "REDD+"), ("Katingan Peatland Restoration", "REDD+"),
    ("West Papua Rainforest Shield", "REDD+"), ("Ucayali Amazon REDD+", "REDD+"),
    ("Madre de Dios Forest Guard", "REDD+"), ("Chocó Biodiversity Corridor", "REDD+"),
    ("Mai-Ndombe REDD+ Congo Basin", "REDD+"), ("Prey Lang Wildlife Sanctuary", "REDD+"),
    ("Gujarat Solar Power Plant", "Renewable Energy"), ("Rajasthan Wind Farm Cluster", "Renewable Energy"),
    ("Tamil Nadu Solar Park", "Renewable Energy"), ("Yunnan Hydropower Station", "Renewable Energy"),
    ("Oregon Biochar Carbon Removal", "Biochar"), ("Mato Grosso Biochar Initiative", "Biochar"),
    ("Vietnam Methane Recovery Swine", "Methane Avoidance"), ("Lam Dong Methane Capture", "Methane Avoidance"),
    ("Papua New Guinea Mangrove Blue Carbon", "Blue Carbon"), ("Colombia Pacific Mangrove Restoration", "Blue Carbon"),
    ("Ethiopia Community Reforestation", "ARR"), ("Sumatra Peatland Reforestation", "ARR"),
    ("Mexico Chiapas Reforestation", "ARR"), ("Cambodia Mondulkiri Restoration", "ARR"),
    ("Thailand Community Cookstoves", "Cookstove"), ("Philippines Clean Cooking", "Cookstove"),
    ("Tanintharyi Conservation", "REDD+"), ("Palawan Forest Protection", "REDD+"),
    ("Guyana Iwokrama Rainforest", "REDD+"), ("Central Kalimantan Peat Protection", "REDD+"),
    ("Chiang Mai Biomass Energy", "Renewable Energy"), ("India Mangrove Gujarat", "Blue Carbon"),
    ("Vietnam Highland Reforestation", "ARR"), ("Peru Andean Reforestation", "ARR"),
    ("Myanmar Coastal Mangroves", "Blue Carbon"), ("Colombia Coffee Agroforestry", "ARR"),
    ("Kilosa Methane Avoidance", "Methane Avoidance"), ("Bangladesh Tidal River Management", "Other"),
    ("Nepal Terai Wetland Restoration", "Other"), ("Petén Maya Biosphere Reserve", "REDD+"),
    ("Madagascar Eastern Rainforest", "REDD+"), ("Amazonas Deep Forest Protection", "REDD+"),
    ("Indonesia Coral Triangle Blue Carbon", "Blue Carbon"), ("Brazil Cerrado Savanna Restoration", "ARR"),
    ("Congo Basin Forest Alliance", "REDD+"), ("Mozambique Coastal Blue Carbon", "Blue Carbon"),
    ("Amhara Landscape Restoration", "ARR"), ("Karnataka Wind Power Project", "Renewable Energy"),
    ("Sichuan Small Hydro Clean Energy", "Renewable Energy"), ("Bahia Atlantic Forest Restoration", "ARR"),
    ("Minas Gerais Cerrado Reforestation", "ARR"), ("Java Mangrove Restoration", "Blue Carbon"),
    ("Luzon Solar Park", "Renewable Energy"), ("Bangkok Biomass Energy", "Renewable Energy"),
    ("Oregon Advanced Biochar II", "Biochar"), ("Nepal Bagmati Reforestation", "ARR"),
    ("Guyana Essequibo Forest Shield", "REDD+"), ("Papua New Guinea Highland REDD+", "REDD+"),
    ("Guatemala Lacandón Forest", "REDD+"), ("Honduras Cloud Forest Protection", "REDD+"),
]

_MEDIUM_NAMES_VERRA = [
    ("Mato Grosso Soy-Free Zone", "REDD+"), ("Kalimantan Degraded Peatland", "REDD+"),
    ("Sumatra Mixed-Use Forest", "REDD+"), ("Peru Lowland Buffer Zone", "REDD+"),
    ("Colombia Caquetá Frontier", "REDD+"), ("India Solar Micro-Grid Pilot", "Renewable Energy"),
    ("Vietnam Small Wind Pilot", "Renewable Energy"), ("Cambodia Rice Husk Energy", "Renewable Energy"),
    ("Kenya Charcoal Transition", "Cookstove"), ("Uganda Improved Kiln Project", "Cookstove"),
    ("Tanzania Sisal Biogas", "Methane Avoidance"), ("Ghana Cocoa Shade Trees", "ARR"),
    ("Senegal Mangrove Pilot", "Blue Carbon"), ("Madagascar Vanilla Agroforestry", "ARR"),
    ("Myanmar Delta Mangrove Pilot", "Blue Carbon"), ("Philippines Bamboo Carbon", "ARR"),
    ("Mexico Oaxaca Community Forest", "REDD+"), ("Guatemala Agroforestry Pilot", "ARR"),
    ("Brazil Pantanal Wetland Pilot", "Blue Carbon"), ("Indonesia Sulawesi Seagrass", "Blue Carbon"),
    ("Ethiopia Rift Valley Restoration", "ARR"), ("Mozambique Cashew Agroforestry", "ARR"),
    ("Nepal Hill Reforestation Pilot", "ARR"), ("Bangladesh Sundarbans Buffer", "REDD+"),
    ("China Guizhou Karst Restoration", "ARR"), ("Thailand Rubber Transition", "ARR"),
    ("Turkey Anatolian Wind Pilot", "Renewable Energy"), ("Morocco Solar Thermal Pilot", "Renewable Energy"),
    ("South Africa Biochar Pilot", "Biochar"), ("Mali Sahel Regreening", "ARR"),
]

_BAD_NAMES_VERRA = [
    ("Suspicious Forestry Credits LLC", "REDD+"), ("Phantom Carbon Offsets Inc", "REDD+"),
    ("Questionable Reforestation Ltd", "ARR"), ("Dubious Credits International", "REDD+"),
    ("Shadow Forest Holdings", "REDD+"), ("Unverified Carbon Solutions", "Other"),
    ("Ghost Project Alpha", "REDD+"), ("Fictitious Mangrove Corp", "Blue Carbon"),
    ("Paper Tiger Conservation", "REDD+"), ("Hollow Green Credits SA", "ARR"),
]

_GOOD_NAMES_GS = [
    ("Kenya Improved Cookstoves Programme", "Cookstove"), ("Uganda Clean Cooking Initiative", "Cookstove"),
    ("Rwanda Efficient Stoves Project", "Cookstove"), ("Ghana LPG Transition Programme", "Cookstove"),
    ("Malawi Cookstove Distribution", "Cookstove"), ("Senegal Clean Cooking Access", "Cookstove"),
    ("Mali Improved Stoves Project", "Cookstove"), ("Burkina Faso Household Energy", "Cookstove"),
    ("India Maharashtra Clean Cooking", "Cookstove"), ("India UP Biomass Cookstoves", "Cookstove"),
    ("Nepal Community Cookstoves", "Cookstove"), ("Bangladesh Improved Cookstoves", "Cookstove"),
    ("Honduras Clean Cooking Programme", "Cookstove"), ("Nicaragua Efficient Stoves", "Cookstove"),
    ("Peru Clean Cooking Initiative", "Cookstove"),
    ("Kenya Solar Home Systems", "Renewable Energy"), ("Uganda Solar Mini-Grid", "Renewable Energy"),
    ("Ghana Wind Power Project", "Renewable Energy"), ("India Karnataka Solar Farm", "Renewable Energy"),
    ("Vietnam Solar Rooftop Programme", "Renewable Energy"), ("Turkey Wind Energy Expansion", "Renewable Energy"),
    ("Morocco Solar Power Plant", "Renewable Energy"), ("South Africa Wind Farm", "Renewable Energy"),
    ("China Sichuan Small Hydro", "Renewable Energy"), ("Philippines Luzon Solar Park", "Renewable Energy"),
    ("Kenya Safe Water Programme", "Other"), ("Uganda Borehole Water Project", "Other"),
    ("Rwanda Water Purification", "Other"), ("Ghana WASH Initiative", "Other"),
    ("Tanzania Waste Management", "Other"),
    ("Colombia Nariño Mangrove Blue Carbon", "Blue Carbon"), ("Colombia Antioquia Reforestation", "ARR"),
    ("Brazil Bahia Atlantic Forest GS", "ARR"), ("Brazil Minas Cerrado GS Reforestation", "ARR"),
    ("Indonesia Java Mangrove GS", "Blue Carbon"), ("Thailand Coastal Mangrove GS", "Blue Carbon"),
    ("Mozambique Maputo Mangrove GS", "Blue Carbon"), ("Tanzania Dar es Salaam Blue Carbon", "Blue Carbon"),
    ("India Biochar Soil Enhancement", "Biochar"), ("Kenya Biochar Agricultural Waste", "Biochar"),
    ("Bangladesh Biogas Methane Recovery", "Methane Avoidance"), ("India Dairy Farm Methane Capture", "Methane Avoidance"),
    ("Vietnam Pig Farm Biogas", "Methane Avoidance"), ("Ghana Landfill Methane Recovery", "Methane Avoidance"),
    ("Zambia Community Forestry REDD+", "REDD+"), ("Malawi Forest Conservation", "REDD+"),
    ("Senegal Mangrove REDD+", "REDD+"), ("Uganda Mountain Gorilla Forest", "REDD+"),
    ("Rwanda Nyungwe Forest Protection", "REDD+"), ("Ghana Cocoa Forest REDD+", "REDD+"),
    ("Kenya Mau Forest Restoration", "ARR"), ("Uganda Albertine Rift Reforestation", "ARR"),
    ("Tanzania Usambara Mountains ARR", "ARR"), ("Malawi Lake Shore Reforestation", "ARR"),
    ("Zambia Miombo Woodland Protection", "REDD+"), ("Senegal Casamance Mangrove", "Blue Carbon"),
    ("India Tamil Nadu Coastal Mangrove", "Blue Carbon"), ("Nepal Himalayan Reforestation", "ARR"),
    ("Honduras Lenca Community Stoves", "Cookstove"), ("Nicaragua Solar Micro-Grid", "Renewable Energy"),
]

_MEDIUM_NAMES_GS = [
    ("Kenya Turkana Solar Pilot", "Renewable Energy"), ("Uganda Karamoja Cookstove Pilot", "Cookstove"),
    ("Rwanda Biogas Pilot Project", "Methane Avoidance"), ("Ghana Volta Basin Restoration", "ARR"),
    ("Malawi Tobacco Transition Stoves", "Cookstove"), ("Zambia Charcoal Alternative", "Cookstove"),
    ("Senegal Peanut Shell Biochar", "Biochar"), ("Mali Niger River Restoration", "ARR"),
    ("Burkina Faso Solar Irrigation", "Renewable Energy"), ("India Odisha Mangrove Pilot", "Blue Carbon"),
    ("Nepal Chitwan Buffer Zone", "REDD+"), ("Bangladesh Haor Wetland Pilot", "Blue Carbon"),
    ("Honduras Mosquitia Forest Pilot", "REDD+"), ("Nicaragua Bosawás Buffer", "REDD+"),
    ("Peru Andes Puna Restoration", "ARR"), ("Colombia Magdalena Reforestation", "ARR"),
    ("Brazil Caatinga Restoration Pilot", "ARR"), ("Indonesia Flores Agroforestry", "ARR"),
    ("Philippines Mindanao Mangrove", "Blue Carbon"), ("Thailand Isaan Biochar Pilot", "Biochar"),
    ("Turkey Black Sea Reforestation", "ARR"), ("Morocco Argan Agroforestry", "ARR"),
    ("South Africa Fynbos Restoration", "Other"), ("Tanzania Pemba Island Blue Carbon", "Blue Carbon"),
    ("Mozambique Gorongosa Buffer", "REDD+"), ("Ethiopia Bale Mountains Pilot", "REDD+"),
    ("Uganda Rwenzori Reforestation", "ARR"), ("Kenya Tana Delta Mangrove", "Blue Carbon"),
    ("Ghana Savanna Restoration Pilot", "ARR"), ("Malawi Mulanje Cedar Restoration", "ARR"),
]

_BAD_NAMES_GS = [
    ("Dubious Clean Cooking Corp", "Cookstove"), ("Phantom Water Credits Ltd", "Other"),
    ("Unverified Stove Distribution", "Cookstove"), ("Ghost Reforestation GS", "ARR"),
    ("Shadow Solar Credits Inc", "Renewable Energy"), ("Fictitious Biogas Project", "Methane Avoidance"),
    ("Paper Forest GS Holdings", "REDD+"), ("Hollow Carbon GS Solutions", "Other"),
    ("Fraudulent Mangrove GS Corp", "Blue Carbon"), ("Fake Cookstove Programme", "Cookstove"),
]


def _make_project(idx, name, ptype, registry, quality_tier):
    """
    Gera um dicionário de projeto com atributos controlados pelo tier de qualidade.
    quality_tier: 'good', 'medium', 'bad'
    """
    country_data = COUNTRIES[idx % len(COUNTRIES)]
    country, region, lat, lon = country_data

    methodologies = VERRA_METHODOLOGIES if registry == "Verra" else GS_METHODOLOGIES
    proponents = PROPONENTS_VERRA if registry == "Verra" else PROPONENTS_GS
    prefix = "VCS" if registry == "Verra" else "GS"

    # ─── Atributos controlados por tier ────────────────────────────
    if quality_tier == "good":
        methodology = random.choice(methodologies.get(ptype, ["VM0004"]))
        proponent = random.choice(proponents)
        start_year = random.randint(2015, 2023)
        end_year = start_year + random.randint(20, 40)
        vintage = random.randint(max(2021, start_year), 2025)
        monitoring = random.choice(["Biannual", "Quarterly"])
        if ptype in ("REDD+", "Blue Carbon", "ARR"):
            area = random.randint(5000, 150000)
            buffer = random.choice([15, 18, 20, 25])
        elif ptype == "Renewable Energy":
            area = random.randint(50, 2000)
            buffer = None
        elif ptype == "Biochar":
            area = random.randint(10, 500)
            buffer = None
        else:
            area = random.randint(100, 5000) if random.random() > 0.3 else None
            buffer = None
        total_issued = random.randint(20000, 5000000)
        retired_pct = random.uniform(0.2, 0.75)
        baseline = f"Baseline validado por auditoria independente para {name} em {country}. Cenário de referência baseado em análise histórica e projeções regionais de uso do solo e emissões. Metodologia {methodology} aplicada com rigor. Verificação de terceira parte completada com sucesso. Dados de sensoriamento remoto e inventário florestal utilizados para calibração do modelo de baseline."
        additionality = f"Análise de adicionalidade demonstra que sem receita de créditos de carbono, o projeto {name} não seria financeiramente viável. Barreiras de investimento, tecnológicas e institucionais identificadas e documentadas. Teste de investimento e análise de cenário alternativo realizados conforme metodologia {methodology}. Aprovado por organismo de validação credenciado."
        desc = _gen_description(name, ptype, country, area or 0, registry)

    elif quality_tier == "medium":
        methodology = random.choice(methodologies.get(ptype, ["VM0004"]))
        proponent = random.choice(proponents)
        start_year = random.randint(2010, 2018)
        end_year = start_year + random.randint(10, 20)
        vintage = random.randint(max(2016, start_year), 2021)
        monitoring = "Annual"
        if ptype in ("REDD+", "Blue Carbon", "ARR"):
            area = random.randint(1000, 30000)
            buffer = random.choice([5, 8, 10])
        elif ptype == "Renewable Energy":
            area = random.randint(20, 500)
            buffer = None
        elif ptype == "Biochar":
            area = random.randint(5, 100)
            buffer = None
        else:
            area = None
            buffer = None
        total_issued = random.randint(50000, 3000000)
        retired_pct = random.uniform(0.3, 0.85)
        baseline = f"Baseline para {name} em {country}. Cenário de referência definido."
        additionality = f"Adicionalidade do projeto {name} documentada."
        desc = _gen_description(name, ptype, country, area or 0, registry)

    else:  # bad
        methodology = None
        proponent = None
        start_year = random.randint(2005, 2012)
        end_year = start_year + random.randint(5, 10)
        vintage = random.randint(2008, 2015)
        monitoring = None
        if ptype in ("REDD+", "Blue Carbon", "ARR"):
            area = random.randint(500, 5000) if random.random() > 0.5 else None
            buffer = random.choice([0, 1, 2]) if area else None
        else:
            area = None
            buffer = None
        total_issued = random.randint(100000, 8000000)
        retired_pct = random.uniform(0.90, 0.99)
        baseline = None
        additionality = None
        desc = "Projeto com documentação limitada e informações insuficientes para verificação completa. Dados de monitoramento ausentes."

    total_retired = int(total_issued * retired_pct)
    total_available = total_issued - total_retired

    return {
        "external_id": f"{prefix}-{1000 + idx * 23}",
        "name": name,
        "description": desc,
        "project_type": ptype,
        "methodology": methodology,
        "registry": registry,
        "country": country,
        "region": region,
        "latitude": lat + random.uniform(-0.5, 0.5),
        "longitude": lon + random.uniform(-0.5, 0.5),
        "start_date": datetime(start_year, random.randint(1, 12), 1, tzinfo=timezone.utc),
        "end_date": datetime(end_year, 12, 31, tzinfo=timezone.utc),
        "proponent": proponent,
        "total_credits_issued": total_issued,
        "total_credits_retired": total_retired,
        "total_credits_available": total_available,
        "vintage_year": vintage,
        "area_hectares": area,
        "baseline_scenario": baseline,
        "additionality_justification": additionality,
        "monitoring_frequency": monitoring,
        "buffer_pool_percentage": buffer,
    }


def _generate_projects():
    """Gera 200 projetos: 100 Verra + 100 Gold Standard com distribuição de qualidade."""
    projects = []
    idx = 0

    # ─── 100 Projetos Verra ────────────────────────────────────────
    # 60 bons, 30 medianos, 10 ruins
    for name, ptype in _GOOD_NAMES_VERRA:
        projects.append(_make_project(idx, name, ptype, "Verra", "good"))
        idx += 1

    for name, ptype in _MEDIUM_NAMES_VERRA:
        projects.append(_make_project(idx, name, ptype, "Verra", "medium"))
        idx += 1

    for name, ptype in _BAD_NAMES_VERRA:
        projects.append(_make_project(idx, name, ptype, "Verra", "bad"))
        idx += 1

    # ─── 100 Projetos Gold Standard ────────────────────────────────
    # 60 bons, 30 medianos, 10 ruins
    for name, ptype in _GOOD_NAMES_GS:
        projects.append(_make_project(idx, name, ptype, "Gold Standard", "good"))
        idx += 1

    for name, ptype in _MEDIUM_NAMES_GS:
        projects.append(_make_project(idx, name, ptype, "Gold Standard", "medium"))
        idx += 1

    for name, ptype in _BAD_NAMES_GS:
        projects.append(_make_project(idx, name, ptype, "Gold Standard", "bad"))
        idx += 1

    return projects


SEED_PROJECTS = _generate_projects()

# ─── Créditos: 2 por projeto (400 total) ──────────────────────────────

PRICES_BY_TYPE = {
    "REDD+": (5.0, 18.0), "ARR": (8.0, 22.0), "Renewable Energy": (3.0, 8.0),
    "Cookstove": (10.0, 25.0), "Methane Avoidance": (5.0, 12.0),
    "Blue Carbon": (15.0, 35.0), "Biochar": (80.0, 150.0),
    "Direct Air Capture": (200.0, 600.0), "Other": (5.0, 15.0),
}


def _generate_credits():
    """Gera créditos para todos os 200 projetos."""
    credits = []
    for proj_idx, proj in enumerate(SEED_PROJECTS):
        ptype = proj["project_type"]
        price_range = PRICES_BY_TYPE.get(ptype, (5.0, 15.0))
        price = round(random.uniform(*price_range), 2)
        ext_id = proj["external_id"]
        vintage = proj["vintage_year"]

        avail = max(1000, proj["total_credits_available"])
        qty1 = random.randint(500, avail // 2 + 1)
        qty2 = random.randint(300, max(400, avail // 3))

        credits.append({
            "project_idx": proj_idx,
            "serial_number": f"{ext_id}-{vintage}-001",
            "vintage_year": vintage,
            "quantity": qty1,
            "status": "active",
            "price_usd": price,
        })
        credits.append({
            "project_idx": proj_idx,
            "serial_number": f"{ext_id}-{vintage}-002",
            "vintage_year": vintage,
            "quantity": qty2,
            "status": "active",
            "price_usd": round(price * random.uniform(0.9, 1.1), 2),
        })

    return credits


SEED_CREDITS = _generate_credits()
