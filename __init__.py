# poi_invariants_pro/__init__.py
__all__ = ["__version__"]
from importlib.resources import files
__version__ = files(__package__).joinpath("VERSION").read_text().strip()
