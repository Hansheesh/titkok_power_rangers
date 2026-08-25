from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

from .interfaces import Product
from .text import flatten_text


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return None


class CatalogIndex:
    """In-memory FTS5 index over the organizer's frozen text catalog."""

    def __init__(self, catalog_path: str | Path) -> None:
        self.catalog_path = Path(catalog_path)
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"Catalog not found at {self.catalog_path}. "
                "Place the organizer-provided catalog at data/catalog.jsonl "
                "or pass a different path to Agent(...)."
            )

        self.connection = sqlite3.connect(":memory:")
        self.products: dict[str, Product] = {}
        self._popular_ids: list[str] = []
        self._build()

    def _build(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products_fts USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )

        batch: list[tuple[str, str, str, str, str, str, str]] = []
        with self.catalog_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw = json.loads(line)
                product = Product(
                    parent_asin=str(raw["parent_asin"]),
                    title=flatten_text(raw.get("title")),
                    categories=flatten_text(raw.get("categories")),
                    features=flatten_text(raw.get("features")),
                    details=flatten_text(raw.get("details")),
                    store=flatten_text(raw.get("store")),
                    description=flatten_text(raw.get("description")),
                    price=_to_float(raw.get("price")),
                    average_rating=_to_float(raw.get("average_rating")),
                    rating_number=_to_int(raw.get("rating_number")),
                    raw=raw,
                )
                self.products[product.parent_asin] = product
                batch.append(
                    (
                        product.parent_asin,
                        product.title,
                        product.categories,
                        product.features,
                        product.details,
                        product.store,
                        product.description,
                    )
                )
                if len(batch) >= 1000:
                    cursor.executemany(
                        "INSERT INTO products_fts VALUES (?, ?, ?, ?, ?, ?, ?)", batch
                    )
                    batch.clear()

        if batch:
            cursor.executemany(
                "INSERT INTO products_fts VALUES (?, ?, ?, ?, ?, ?, ?)", batch
            )
        self.connection.commit()

        self._popular_ids = sorted(
            self.products,
            key=lambda asin: self._quality_prior(self.products[asin]),
            reverse=True,
        )[:500]

    @staticmethod
    def _quality_prior(product: Product) -> float:
        rating = product.average_rating or 0.0
        count = max(0, product.rating_number or 0)
        return rating + 0.15 * math.log1p(count)

    def get(self, parent_asin: str) -> Product:
        return self.products[parent_asin]

    def popular(self, limit: int) -> list[str]:
        return self._popular_ids[:limit]

    def search(
        self,
        expression: str,
        limit: int,
        field_weights: tuple[float, ...],
    ) -> list[str]:
        """Run one weighted FTS route and return IDs in route-rank order."""

        if not expression:
            return []

        sql = (
            "SELECT parent_asin FROM products_fts "
            "WHERE products_fts MATCH ? "
            f"ORDER BY bm25(products_fts, {', '.join(str(v) for v in field_weights)}) "
            "LIMIT ?"
        )
        try:
            rows = self.connection.execute(sql, (expression, limit)).fetchall()
        except sqlite3.OperationalError:
            # A malformed/over-constrained query must degrade to another route,
            # not crash the session.
            return []
        return [str(row[0]) for row in rows]
