"""Activación segura de los parches POPIS.

Guarda referencias al motor base ANTES de reemplazar funciones. Esto evita
recursión cuando un wrapper necesita reutilizar la implementación original.
"""
from __future__ import annotations

import numpy as np
import popis_core as core

_ORIGINAL_LABORATORY = core.laboratory_indicators


def activate() -> None:
    from popis_core_patch import apply_patches
    from popis_suive_fix import parse_suive_history as robust_parse_suive_history
    from popis_case_population_fix import activate_case_population_fixes

    apply_patches()

    # Corregir el cruce con las bases reales antes de cargar fuentes locales:
    # - Edo_Res -> residencia Sonora
    # - pobm/pobh_65_mm -> 65+
    # - casos >=65 -> denominador 65+ cuando corresponda.
    activate_case_population_fixes()

    # El libro de canal endémico repite años en las secciones de casos e
    # incidencia. La versión robusta obliga a seleccionar conteos de casos y
    # recorta ceros de semanas futuras del año actual.
    core.parse_suive_history = robust_parse_suive_history

    def laboratory_indicators(df, year: int, month: int):
        result = _ORIGINAL_LABORATORY(df, year, month).copy()
        reject = result["Indicador"].eq("Muestras rechazadas")
        if reject.any():
            result.loc[reject, "Escala"] = np.where(
                result.loc[reject, "Cumple"].eq("Sí"),
                "Cumple estándar ≤10%",
                "Alarma >10%",
            )
        return result

    core.laboratory_indicators = laboratory_indicators
