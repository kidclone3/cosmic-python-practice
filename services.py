from __future__ import annotations

from datetime import date

import model
from model import OrderLine
from repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref

def add_batch(
    reference: str,
    sku: str,
    qty: int,
    eta: date | None,
    repo: AbstractRepository,
    session,
) -> None:
    batch = model.Batch(reference, sku, qty, eta)
    repo.add(batch)
    session.commit()

def deallocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")

    batchref = model.deallocate(line, batches)
    session.commit()
    return batchref
