from datetime import datetime
from flask import Flask, jsonify, request

from allocation.domain import model
from allocation.adapters import orm
from allocation.service_layer import services, unit_of_work

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    services.add_batch(
        request.json['ref'], request.json['sku'], request.json['qty'], eta,
        uow
    )
    return 'OK', 201


@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        batchref = services.allocate(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty'],
            uow,
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batchref': batchref}), 201
