import os
from flask import redirect
from db import db
from flask_cors import CORS
from flask import Flask
from flask_smorest import Api
from resources.carts import blp as CartBlueprint
from resources.orders import blp as OrderBlueprint
from resources.products import blp as ProductBlueprint


def create_app(db_url=None):

    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "SHOPPING REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv(
        "DATABASE_URL",
        "postgresql://admin:admin@postgres:5432/shopping_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    api = Api(app)

    CORS(app)

    # Init for the database
    @app.before_request
    def create_tables():
        app.before_request_funcs[None].remove(create_tables)
        db.create_all()

    # Redirecting the route for the Swagger docs
    @app.route("/")
    def home():
        return redirect("/docs")

    api.register_blueprint(OrderBlueprint)
    api.register_blueprint(CartBlueprint)
    api.register_blueprint(ProductBlueprint)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)