from flask.views import MethodView
from flask_smorest import Blueprint, abort
import requests

blp = Blueprint("Products", __name__, description="Operations on products")


def fetch_all_products():
    """Fetch all products from Fake Store API."""
    try:
        response = requests.get("https://fakestoreapi.com/products", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        abort(504, message="Fake Store API timeout")
    except requests.RequestException:
        abort(500, message="Failed to fetch products from Fake Store API")


@blp.route("/products")
class ProductList(MethodView):
    def get(self):
        """Fetch all available products from the Fake Store API."""
        products = fetch_all_products()
        if products:
            return products
        else:
            abort(500, message="Failed to fetch products from Fake Store API")
