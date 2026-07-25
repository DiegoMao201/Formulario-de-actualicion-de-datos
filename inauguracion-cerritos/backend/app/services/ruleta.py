"""Lógica SEGURA de la ruleta. El resultado se decide SIEMPRE en el servidor.

- Selección ponderada por `probabilidad` de cada premio activo con stock.
- `server_seed` firmado -> provably fair (auditable).
- Se descuenta stock de forma atómica dentro de la transacción del llamador.
"""
import hashlib
import secrets as _secrets
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Prize


def _generar_seed() -> str:
    return hashlib.sha256(_secrets.token_bytes(32)).hexdigest()


def segmentos_visibles(db: Session, channel_id: Optional[str] = None) -> List[Prize]:
    """Premios activos de un canal (o de la inauguración si channel_id es None)."""
    q = db.query(Prize).filter(Prize.activo.is_(True))
    if channel_id is None:
        q = q.filter(Prize.channel_id.is_(None))
    else:
        q = q.filter(Prize.channel_id == channel_id)
    return q.order_by(Prize.orden.asc(), Prize.created_at.asc()).all()


def elegir_premio(
    db: Session, channel_id: Optional[str] = None
) -> Tuple[Optional[Prize], str, int, List[Prize]]:
    """Devuelve (premio, server_seed, indice_segmento, lista_segmentos).

    - Solo entran al sorteo premios con stock_restante > 0 (o perdedores, stock infinito).
    - La ponderación usa `probabilidad`. Si todo lo "ganable" se agotó, cae en un perdedor.
    """
    seed = _generar_seed()
    segmentos = segmentos_visibles(db, channel_id)
    if not segmentos:
        return None, seed, 0, []

    # Candidatos elegibles: perdedores siempre; ganables solo con stock.
    elegibles = [
        p for p in segmentos
        if p.es_perdedor or p.stock_restante > 0
    ]
    if not elegibles:
        elegibles = [p for p in segmentos if p.es_perdedor] or segmentos

    pesos = [max(p.probabilidad, 0.0) for p in elegibles]
    total = sum(pesos)
    if total <= 0:
        # Sin probabilidades definidas: reparto uniforme.
        pesos = [1.0] * len(elegibles)
        total = float(len(elegibles))

    # Punto de corte derivado del seed (determinista y auditable).
    r = (int(seed[:8], 16) / 0xFFFFFFFF) * total
    acumulado = 0.0
    elegido = elegibles[-1]
    for p, w in zip(elegibles, pesos):
        acumulado += w
        if r <= acumulado:
            elegido = p
            break

    indice = segmentos.index(elegido)
    return elegido, seed, indice, segmentos
