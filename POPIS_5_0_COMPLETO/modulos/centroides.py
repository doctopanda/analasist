from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

# Centroides/cabeceras municipales de respaldo para Sonora.
# Cuando existe GeoJSON municipal, POPIS calcula el centroide del polígono y lo prioriza.
CENTROIDES_SONORA: dict[str, tuple[float, float]] = {
    "ACONCHI": (29.8333, -110.2333),
    "AGUA PRIETA": (31.3353, -109.5503),
    "ALAMOS": (27.0167, -108.9333),
    "ALTAR": (30.7167, -111.8333),
    "ARIVECHI": (29.5000, -109.1833),
    "ARIZPE": (30.3333, -110.1667),
    "ATIL": (30.8500, -111.5333),
    "BACADEHUACHI": (29.8083, -109.1403),
    "BACANORA": (28.9825, -109.4000),
    "BACERAC": (30.2167, -108.9167),
    "BACOACHI": (30.6167, -109.9667),
    "BACUM": (27.5333, -110.0667),
    "BANAMICHI": (30.0000, -110.2167),
    "BAVIACORA": (29.6667, -110.1667),
    "BAVISPE": (30.4500, -108.9333),
    "BENJAMIN HILL": (30.1667, -111.1000),
    "CABORCA": (30.7145, -112.1616),
    "CAJEME": (27.4961, -109.9328),
    "CANANEA": (30.9833, -110.3000),
    "CARBO": (29.6833, -110.9667),
    "LA COLORADA": (28.8333, -109.9167),
    "CUCURPE": (30.3333, -110.7167),
    "CUMPAS": (30.0167, -109.7833),
    "DIVISADEROS": (29.6833, -109.1167),
    "EMPALME": (27.9511, -110.7789),
    "ETCHOJOA": (26.9000, -109.6333),
    "FRONTERAS": (30.8500, -109.5167),
    "GENERAL PLUTARCO ELIAS CALLES": (32.0000, -114.5000),
    "GRANADOS": (29.8667, -109.3500),
    "GUAYMAS": (27.9219, -110.8987),
    "HERMOSILLO": (29.0729, -110.9559),
    "HUACHINERA": (30.1667, -108.9333),
    "HUASABAS": (29.8500, -109.3167),
    "HUATABAMPO": (26.8167, -109.6333),
    "HUEPAC": (29.9111, -110.2178),
    "IMURIS": (30.7833, -110.8500),
    "MAGDALENA": (30.6167, -110.9667),
    "MAZATAN": (29.0167, -110.1333),
    "MOCTEZUMA": (29.8000, -109.6833),
    "NACO": (31.3333, -109.9500),
    "NACORI CHICO": (29.6886, -109.1572),
    "NACOZARI DE GARCIA": (30.3833, -109.6833),
    "NAVOJOA": (27.0728, -109.4437),
    "NOGALES": (31.3167, -110.9333),
    "ONAVAS": (28.4667, -109.5333),
    "OPODEPE": (29.9333, -110.6167),
    "OQUITOA": (30.8167, -111.8833),
    "PITIQUITO": (30.6833, -112.0500),
    "PUERTO PENASCO": (31.3167, -113.5333),
    "QUIRIEGO": (27.5167, -109.2500),
    "RAYON": (29.7167, -110.5667),
    "ROSARIO": (27.2000, -109.2333),
    "SAHUARIPA": (29.0333, -109.2500),
    "SAN FELIPE DE JESUS": (29.7000, -110.6833),
    "SAN JAVIER": (29.5833, -110.0667),
    "SAN LUIS RIO COLORADO": (32.4519, -114.7641),
    "SAN MIGUEL DE HORCASITAS": (29.4833, -110.6667),
    "SAN PEDRO DE LA CUEVA": (29.2833, -109.7833),
    "SANTA ANA": (30.5406, -111.1223),
    "SANTA CRUZ": (31.3667, -110.5667),
    "SARIC": (30.9667, -111.4167),
    "SOYOPA": (29.2000, -109.8000),
    "SUAQUI GRANDE": (28.8000, -109.9333),
    "TEPACHE": (29.6167, -109.2667),
    "TRINCHERAS": (30.3667, -111.5333),
    "TUBUTAMA": (30.8833, -111.6167),
    "URES": (29.4333, -110.3833),
    "VILLA HIDALGO": (30.1833, -108.9500),
    "VILLA PESQUEIRA": (29.1000, -110.0833),
    "YECORA": (28.3667, -108.9333),
    "BENITO JUAREZ": (27.0167, -109.5000),
    "SAN IGNACIO RIO MUERTO": (27.4000, -110.2167),
}

ALIASES = {
    "PLUTARCO ELIAS CALLES": "GENERAL PLUTARCO ELIAS CALLES",
    "GRAL PLUTARCO ELIAS CALLES": "GENERAL PLUTARCO ELIAS CALLES",
    "GRAL. PLUTARCO ELIAS CALLES": "GENERAL PLUTARCO ELIAS CALLES",
    "PUERTO PENASCO": "PUERTO PENASCO",
    "SAN LUIS RIO COLORADO": "SAN LUIS RIO COLORADO",
    "NACOZARI DE GARCIA": "NACOZARI DE GARCIA",
}


def norm(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper().strip()
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return ALIASES.get(text, text)


def _ring_centroid(coords: list) -> tuple[float, float] | None:
    # Centroide geométrico básico del anillo exterior. Suficiente para visualización epidemiológica.
    try:
        ring = coords[0]
        if not ring:
            return None
        xs = [float(p[0]) for p in ring]
        ys = [float(p[1]) for p in ring]
        return sum(ys) / len(ys), sum(xs) / len(xs)
    except Exception:
        return None


def centroids_from_geojson(geojson: dict | None) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    if not geojson:
        return out
    name_candidates = ["NOMGEO", "NOM_MUN", "NOM_MUNICIPIO", "MUNICIPIO", "Municipio", "name", "NAME_2"]
    for feature in geojson.get("features", []) or []:
        props = feature.get("properties") or {}
        name = next((props.get(k) for k in name_candidates if props.get(k)), None)
        if not name:
            continue
        geom = feature.get("geometry") or {}
        typ = geom.get("type")
        coords = geom.get("coordinates") or []
        centroid = None
        if typ == "Polygon" and coords:
            centroid = _ring_centroid(coords)
        elif typ == "MultiPolygon" and coords:
            pieces = []
            for poly in coords:
                c = _ring_centroid(poly)
                if c:
                    pieces.append(c)
            if pieces:
                centroid = (sum(x[0] for x in pieces) / len(pieces), sum(x[1] for x in pieces) / len(pieces))
        if centroid:
            out[norm(name)] = centroid
    return out


def resolve_centroid(municipio: Any, geo_centroids: dict[str, tuple[float, float]] | None = None) -> tuple[float | None, float | None, str]:
    key = norm(municipio)
    if geo_centroids and key in geo_centroids:
        lat, lon = geo_centroids[key]
        return float(lat), float(lon), "Centroide municipal GeoJSON"
    if key in CENTROIDES_SONORA:
        lat, lon = CENTROIDES_SONORA[key]
        return float(lat), float(lon), "Centroide municipal interno"
    for known, value in CENTROIDES_SONORA.items():
        if key and (known in key or key in known):
            return float(value[0]), float(value[1]), "Centroide municipal interno"
    return None, None, "Sin centroide"


def apply_centroids(df: pd.DataFrame, municipio_col: str = "Mun_Res", geojson: dict | None = None) -> pd.DataFrame:
    out = df.copy()
    geo_centroids = centroids_from_geojson(geojson)
    rows = [resolve_centroid(v, geo_centroids) for v in out.get(municipio_col, pd.Series(index=out.index, dtype=object))]
    out["__lat_centroide"] = [r[0] for r in rows]
    out["__lon_centroide"] = [r[1] for r in rows]
    out["__fuente_centroide"] = [r[2] for r in rows]
    return out
