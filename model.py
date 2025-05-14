import dataclasses


class Batch:
    def __init__(self, reference: str, sku: str, qty: int, eta=None):
        self.reference = reference
        self.sku = sku
        self.eta = eta
        self._allocations = set()
        self._qty = qty

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

    def allocate(self, line):
        if self.can_allocate(line):
            self._allocations.add(line)
            self._qty -= line.qty

    @property
    def available_quantity(self):
        return self._qty

    def can_allocate(self, line):
        return line.sku == self.sku and line.qty <= self.available_quantity

@dataclasses.dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


def allocate(line: OrderLine, batches: list[Batch]):
    """Allocate the order line to the first batch that can fulfill it."""

    batch = next(b for b in sorted(batches) if b.can_allocate(line))
    batch.allocate(line)
    return batch.reference