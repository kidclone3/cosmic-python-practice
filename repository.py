import abc

from sqlalchemy import text

import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def _add_or_update_batch(self, batch):
        result = self.session.execute(
            text("""
            INSERT INTO batches (reference, sku, _purchased_quantity, eta)
            VALUES (:reference, :sku, :_purchased_quantity, :eta)
            ON CONFLICT(reference) DO UPDATE SET
                        sku = excluded.sku,
                        _purchased_quantity = excluded._purchased_quantity,
                        eta = excluded.eta
            """),
            {
                "reference": batch.reference,
                "sku": batch.sku,
                "_purchased_quantity": batch._purchased_quantity,
                "eta": batch.eta,
            },
        )
        self.session.commit()

        # Try getting the id via lastrowid.
        batch_id = result.lastrowid
        if batch_id is None:
            # Conflict occurred, so fetch id manually
            batch_id_row = self.session.execute(
                "SELECT id FROM batches WHERE reference = :reference",
                {"reference": batch.reference},
            ).fetchone()
            batch_id = batch_id_row[0] if batch_id_row else None

        return batch_id

    def _add_or_update_order_line(self, order_line):
        result = self.session.execute(
            text("""
            INSERT INTO order_lines (orderid, sku, qty)
            VALUES (:orderid, :sku, :qty)
            ON CONFLICT(orderid) DO UPDATE SET
                        sku = excluded.sku,
                        qty = excluded.qty
            """),
            {
                "orderid": order_line.orderid,
                "sku": order_line.sku,
                "qty": order_line.qty,
            },
        )
        self.session.commit()

        # Try getting the id via lastrowid.
        orderline_id = result.lastrowid
        if orderline_id is None:
            # Conflict occurred, so fetch id manually
            orderline_id_row = self.session.execute(
                "SELECT id FROM order_lines WHERE orderid = :orderid",
                {"orderid": order_line.orderid},
            ).fetchone()
            orderline_id = orderline_id_row[0] if orderline_id_row else None

        return orderline_id

    def add(self, batch):
        # self.session.execute('INSERT INTO ??
        batch_id = self._add_or_update_batch(batch)

        # get the lines to be allocated
        for line in batch._allocations:
            orderline_id = self._add_or_update_order_line(line)

            # insert into allocations
            self.session.execute(
                "INSERT INTO allocations (orderline_id, batch_id)"
                " VALUES (:orderline_id, :batch_id)",
                dict(orderline_id=orderline_id, batch_id=batch_id),
            )

        self.session.commit()


    def get(self, reference) -> model.Batch:
        # self.session.execute('SELECT ??
        query = self.session.execute(
            text("""
            SELECT
                b.reference AS batch_reference,
                b.sku AS batch_sku,
                b._purchased_quantity,
                b.eta,
                ol.orderid AS orderline_orderid,
                ol.sku AS orderline_sku,
                ol.qty AS orderline_qty
            FROM
                batches b
                    LEFT JOIN allocations a ON b.id = a.batch_id
                    LEFT JOIN order_lines ol ON a.orderline_id = ol.id
            WHERE
                b.reference = :reference
            """),
            dict(reference=reference),
        )

        rows = query.fetchall()

        if not rows:
            raise model.OutOfStock(f"Batch with reference {reference} not found")

        first = rows[0]
        batch = model.Batch(
            ref=first["batch_reference"],
            sku=first["batch_sku"],
            qty=first["_purchased_quantity"],
            eta=first["eta"],
        )

        # Add allocations
        for row in rows:
            # If there's an allocated order line
            if row["orderline_orderid"] is not None:
                order_line = model.OrderLine(
                    orderid=row["orderline_orderid"],
                    sku=row["orderline_sku"],
                    qty=row["orderline_qty"],
                )
                batch.allocate(order_line)

        return batch
