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
    apply_patches()

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
