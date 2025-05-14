from datetime import date, timedelta
import pytest

from model import Batch, OrderLine, allocate

# from model import ...

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

def make_batch_and_line(sku, batch_qty, line_qty):
    return Batch("batch1", sku, qty=batch_qty, eta=today), OrderLine("order-ref1", sku, qty=line_qty)

def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch("batch1", "SMALL-TABLE", qty=10, eta=today)
    line = OrderLine("order-ref1", "SMALL-TABLE", 2)

    batch.allocate(line)
    assert batch.available_quantity == 8

def test_can_allocate_if_available_greater_than_required():
    large_batch, small_line = make_batch_and_line("SMALL-TABLE", 20, 2)
    assert large_batch.can_allocate(small_line)

def test_cannot_allocate_if_available_smaller_than_required():
    small_batch, large_line = make_batch_and_line("LARGE-TABLE", 1, 2)
    assert not small_batch.can_allocate(large_line)

def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("LARGE-TABLE", 2, 2)
    assert batch.can_allocate(line)


def test_prefers_warehouse_batches_to_shipments():
    instock_batch = Batch("in-stock-batch", "ELEGANT-LAMP", qty=100, eta=None)
    shipment_batch = Batch("shipment-batch", "ELEGANT-LAMP", qty=100, eta=tomorrow)
    line = OrderLine("order-ref", "ELEGANT-LAMP", qty=10)
    allocate(line, [instock_batch, shipment_batch])

    assert instock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest_batch = Batch("speedy", "SMALL-TABLE", qty=100, eta=today)
    medium_batch = Batch("medium", "SMALL-TABLE", qty=100, eta=tomorrow)
    latest_batch = Batch("slow", "SMALL-TABLE", qty=100, eta=later)

    line = OrderLine("oref", "SMALL-TABLE", 10)

    allocate(line, [earliest_batch, medium_batch, latest_batch])
    assert earliest_batch.available_quantity == 90
    assert medium_batch.available_quantity == 100
    assert latest_batch.available_quantity == 100