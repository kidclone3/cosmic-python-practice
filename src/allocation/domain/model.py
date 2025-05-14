from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Set


class OutOfStock(Exception):
    pass


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")


class Product:

    def __init__(self,sku: str, batches: list[Batch], version_number: int = 1, **kwargs):
        self.sku = sku
        self.batches = batches
        self._validate_batches()
        self.version_number = version_number

    def _validate_batch(self, batch):
        if not isinstance(batch, Batch):
            raise TypeError(f"Expected a Batch instance, got {type(batch)}")
        if batch.sku != self.sku:
            raise ValueError(f"Batch {batch.reference} has sku {batch.sku}, expected {self.sku}")

    def _validate_batches(self):
        if not isinstance(self.batches, list):
            raise TypeError(f"Expected a list of Batch instances, got {type(self.batches)}")
        for batch in self.batches:
            self._validate_batch(batch)

    def allocate(self, line):
        """Allocate a line to a batch, returning the batch reference."""
        self.version_number += 1
        return allocate(line, self.batches)

    def get(self, sku):
        return next((batch for batch in self.batches if batch.sku == sku), None)


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()  # type: Set[OrderLine]

    def __repr__(self):
        return f"<Batch {self.reference}>"

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty
