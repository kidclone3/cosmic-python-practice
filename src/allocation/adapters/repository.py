import abc

from sqlalchemy import insert

from allocation.domain import model


class AbstractRepository(abc.ABC):
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()


class SqlAlchemyProductRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def upsert_product(self, sku, version_number):
        stmt = insert(model.Product).values(sku=sku, version_number=version_number)
        stmt = stmt.on_conflict_do_update(
            index_elements=["sku"], set_={"version_number": version_number}
        )
        self.session.execute(stmt)

    def add(self, product):
        # self.session.add(product)
        self.upsert_product(product.sku, product.version_number)

    def update(self, product):
        self.session.merge(product)

    def get(self, sku):
        batches = self.session.query(model.Batch).filter_by(sku=sku).all()
        product= self.session.query(model.Product).filter_by(sku=sku).one_or_none()
        return model.Product(sku, batches, product.version_number) if product else model.Product(sku, batches, 1)