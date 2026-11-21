"""Synthetic supply-chain data generator for SupplyChainIQ.

Produces a deterministic seed dataset - suppliers, products, warehouses,
inventory, shipments and disruption events - shaped closely enough to
``datasets/DataCoSupplyChainDataset.csv`` to stand in for it during
development.

Run from ``SupplyChainIQ/backend``::

    python -m app.services.data_generator
    python -m app.services.data_generator --rows 5000 --seed 7 --out data/seed
    python -m app.services.data_generator --format both

The module depends only on pydantic and the standard library, so it keeps
working while ``app.models`` and ``app.database`` are still empty. Swap the
models below for the real ORM models once those packages exist.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from pydantic import BaseModel, Field

ENTITY_NAMES: tuple[str, ...] = (
    "suppliers",
    "products",
    "warehouses",
    "inventory",
    "shipments",
    "disruptions",
)

SUPPLIER_PREFIXES: tuple[str, ...] = (
    "Northwind", "Apex", "Meridian", "Kestrel", "Vantage", "Ironwood",
    "Blue Harbor", "Solstice", "Cobalt", "Granite", "Lumen", "Redwood",
    "Silverline", "Tessera", "Orchid", "Pinnacle",
)

SUPPLIER_SUFFIXES: tuple[str, ...] = (
    "Logistics", "Components", "Industries", "Supply Co.", "Manufacturing",
    "Trading", "Materials", "Systems",
)

CATEGORY_DEPARTMENTS: dict[str, str] = {
    "Sporting Goods": "Fitness",
    "Electronics": "Technology",
    "Apparel": "Apparel",
    "Health and Beauty": "Health",
    "Home and Garden": "Home",
    "Automotive": "Auto",
    "Books": "Media",
    "Grocery": "Food",
}

PRODUCT_ADJECTIVES: tuple[str, ...] = (
    "Compact", "Pro", "Ultra", "Eco", "Prime", "Flex", "Titan", "Nova",
    "Core", "Edge",
)

PRODUCT_NOUNS: tuple[str, ...] = (
    "Tracker", "Sensor", "Bottle", "Headset", "Backpack", "Lamp", "Kettle",
    "Charger", "Mat", "Jacket", "Monitor", "Blender",
)

# (city, country, region, latitude, longitude)
WAREHOUSE_SITES: tuple[tuple[str, str, str, float, float], ...] = (
    ("Chicago", "United States", "North America", 41.8781, -87.6298),
    ("Dallas", "United States", "North America", 32.7767, -96.7970),
    ("Newark", "United States", "North America", 40.7357, -74.1724),
    ("Rotterdam", "Netherlands", "Europe", 51.9244, 4.4777),
    ("Hamburg", "Germany", "Europe", 53.5511, 9.9937),
    ("Singapore", "Singapore", "Southeast Asia", 1.3521, 103.8198),
    ("Mumbai", "India", "South Asia", 19.0760, 72.8777),
    ("Sao Paulo", "Brazil", "South America", -23.5505, -46.6333),
)

# (mode, scheduled days)
SHIPPING_MODES: tuple[tuple[str, int], ...] = (
    ("Standard Class", 4),
    ("Second Class", 2),
    ("First Class", 1),
    ("Same Day", 0),
)

DELIVERY_STATUSES: tuple[str, ...] = (
    "Advance shipping",
    "Shipping on time",
    "Late delivery",
    "Shipping canceled",
)

DISRUPTION_KINDS: tuple[str, ...] = (
    "port congestion",
    "supplier bankruptcy",
    "extreme weather",
    "cyber incident",
    "customs delay",
    "labor strike",
    "raw material shortage",
    "carrier outage",
)


class Supplier(BaseModel):
    id: str
    name: str
    country: str
    region: str
    tier: int = Field(ge=1, le=3)
    lead_time_days: int = Field(ge=1, le=120)
    reliability_score: float = Field(ge=0.0, le=1.0)
    on_time_rate: float = Field(ge=0.0, le=1.0)
    capacity_units_per_week: int = Field(ge=0)
    active: bool = True


class Product(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    department: str
    supplier_id: str
    unit_price: float = Field(gt=0)
    unit_cost: float = Field(gt=0)
    weight_kg: float = Field(gt=0)
    active: bool = True


class Warehouse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    region: str
    capacity_units: int = Field(gt=0)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class InventoryRecord(BaseModel):
    id: str
    product_id: str
    warehouse_id: str
    on_hand: int = Field(ge=0)
    in_transit: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    safety_stock: int = Field(ge=0)
    updated_at: datetime


class Shipment(BaseModel):
    id: str
    order_id: str
    product_id: str
    supplier_id: str
    warehouse_id: str
    quantity: int = Field(gt=0)
    shipping_mode: str
    scheduled_days: int = Field(ge=0)
    actual_days: int = Field(ge=0)
    late_delivery_risk: int = Field(ge=0, le=1)
    delivery_status: str
    sales: float = Field(ge=0.0)
    benefit_per_order: float
    order_date: datetime
    shipping_date: datetime


class DisruptionEvent(BaseModel):
    id: str
    kind: str
    severity: int = Field(ge=1, le=5)
    region: str
    affected_supplier_ids: list[str]
    started_at: datetime
    resolved_at: datetime | None = None
    description: str


class SeedDataset(BaseModel):
    generated_at: datetime
    seed: int
    suppliers: list[Supplier]
    products: list[Product]
    warehouses: list[Warehouse]
    inventory: list[InventoryRecord]
    shipments: list[Shipment]
    disruptions: list[DisruptionEvent]


class SupplyChainDataGenerator:
    """Deterministic generator: the same seed and anchor yield the same data."""

    def __init__(self, seed: int = 42, anchor: datetime | None = None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.anchor = anchor or datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def generate(self, rows: int = 1000) -> SeedDataset:
        suppliers = self.suppliers(16)
        products = self.products(40, suppliers)
        warehouses = self.warehouses()
        inventory = self.inventory(products, warehouses)
        shipments = self.shipments(rows, products, suppliers, warehouses)
        disruptions = self.disruptions(8, suppliers)
        return SeedDataset(
            generated_at=datetime.now(timezone.utc),
            seed=self.seed,
            suppliers=suppliers,
            products=products,
            warehouses=warehouses,
            inventory=inventory,
            shipments=shipments,
            disruptions=disruptions,
        )

    def suppliers(self, count: int) -> list[Supplier]:
        names = {
            f"{self.rng.choice(SUPPLIER_PREFIXES)} {self.rng.choice(SUPPLIER_SUFFIXES)}"
            for _ in range(count * 3)
        }
        chosen = sorted(names)[:count]
        result: list[Supplier] = []
        for index, name in enumerate(chosen, start=1):
            city, country, region, _, _ = self.rng.choice(WAREHOUSE_SITES)
            reliability = round(self.rng.uniform(0.55, 0.99), 3)
            result.append(
                Supplier(
                    id=f"SUP-{index:04d}",
                    name=name,
                    country=country,
                    region=region,
                    tier=self.rng.choice((1, 1, 2, 2, 3)),
                    lead_time_days=self.rng.randint(3, 60),
                    reliability_score=reliability,
                    on_time_rate=round(min(1.0, reliability + self.rng.uniform(-0.1, 0.05)), 3),
                    capacity_units_per_week=self.rng.randint(500, 25000),
                    active=self.rng.random() > 0.08,
                )
            )
        return result

    def products(self, count: int, suppliers: list[Supplier]) -> list[Product]:
        categories = list(CATEGORY_DEPARTMENTS)
        result: list[Product] = []
        for index in range(1, count + 1):
            category = self.rng.choice(categories)
            price = round(self.rng.uniform(8.0, 899.0), 2)
            result.append(
                Product(
                    id=f"PRD-{index:04d}",
                    sku=f"SKU-{self.rng.randint(100000, 999999)}",
                    name=(
                        f"{self.rng.choice(PRODUCT_ADJECTIVES)} "
                        f"{self.rng.choice(PRODUCT_NOUNS)} {index}"
                    ),
                    category=category,
                    department=CATEGORY_DEPARTMENTS[category],
                    supplier_id=self.rng.choice(suppliers).id,
                    unit_price=price,
                    unit_cost=round(price * self.rng.uniform(0.45, 0.85), 2),
                    weight_kg=round(self.rng.uniform(0.1, 25.0), 2),
                    active=self.rng.random() > 0.05,
                )
            )
        return result

    def warehouses(self) -> list[Warehouse]:
        return [
            Warehouse(
                id=f"WH-{index:03d}",
                name=f"{city} Distribution Center",
                city=city,
                country=country,
                region=region,
                capacity_units=self.rng.randint(50_000, 500_000),
                latitude=latitude,
                longitude=longitude,
            )
            for index, (city, country, region, latitude, longitude) in enumerate(
                WAREHOUSE_SITES, start=1
            )
        ]

    def inventory(
        self, products: list[Product], warehouses: list[Warehouse]
    ) -> list[InventoryRecord]:
        result: list[InventoryRecord] = []
        counter = 0
        for product in products:
            for warehouse in self.rng.sample(warehouses, k=min(3, len(warehouses))):
                counter += 1
                reorder_point = self.rng.randint(50, 400)
                result.append(
                    InventoryRecord(
                        id=f"INV-{counter:05d}",
                        product_id=product.id,
                        warehouse_id=warehouse.id,
                        on_hand=self.rng.randint(0, 1200),
                        in_transit=self.rng.randint(0, 300),
                        reorder_point=reorder_point,
                        safety_stock=int(reorder_point * self.rng.uniform(0.2, 0.6)),
                        updated_at=self.anchor - timedelta(hours=self.rng.randint(0, 72)),
                    )
                )
        return result

    def shipments(
        self,
        count: int,
        products: list[Product],
        suppliers: list[Supplier],
        warehouses: list[Warehouse],
    ) -> list[Shipment]:
        result: list[Shipment] = []
        for index in range(1, count + 1):
            product = self.rng.choice(products)
            mode, scheduled = self.rng.choice(SHIPPING_MODES)
            delay = self.rng.choices(
                (0, 1, 2, 3, 5, 8), weights=(45, 20, 14, 10, 7, 4), k=1
            )[0]
            actual = scheduled + delay
            if delay == 0:
                status = self.rng.choice(("Advance shipping", "Shipping on time"))
            elif self.rng.random() < 0.03:
                status = "Shipping canceled"
            else:
                status = "Late delivery"
            quantity = self.rng.randint(1, 20)
            sales = round(product.unit_price * quantity, 2)
            order_date = self.anchor - timedelta(
                days=self.rng.randint(0, 180), minutes=self.rng.randint(0, 1439)
            )
            result.append(
                Shipment(
                    id=f"SHP-{index:06d}",
                    order_id=f"ORD-{self.rng.randint(10000, 99999)}",
                    product_id=product.id,
                    supplier_id=product.supplier_id,
                    warehouse_id=self.rng.choice(warehouses).id,
                    quantity=quantity,
                    shipping_mode=mode,
                    scheduled_days=scheduled,
                    actual_days=actual,
                    late_delivery_risk=1 if actual > scheduled else 0,
                    delivery_status=status,
                    sales=sales,
                    benefit_per_order=round(sales * self.rng.uniform(-0.1, 0.35), 2),
                    order_date=order_date,
                    shipping_date=order_date + timedelta(days=actual),
                )
            )
        return result

    def disruptions(
        self, count: int, suppliers: list[Supplier]
    ) -> list[DisruptionEvent]:
        result: list[DisruptionEvent] = []
        for index in range(1, count + 1):
            supplier = self.rng.choice(suppliers)
            kind = self.rng.choice(DISRUPTION_KINDS)
            started = self.anchor - timedelta(days=self.rng.randint(1, 120))
            resolved = (
                started + timedelta(days=self.rng.randint(1, 30))
                if self.rng.random() < 0.6
                else None
            )
            result.append(
                DisruptionEvent(
                    id=f"DIS-{index:04d}",
                    kind=kind,
                    severity=self.rng.randint(1, 5),
                    region=supplier.region,
                    affected_supplier_ids=[supplier.id],
                    started_at=started,
                    resolved_at=resolved,
                    description=(
                        f"{kind.capitalize()} affecting {supplier.name} "
                        f"in {supplier.region}."
                    ),
                )
            )
        return result


def _records(dataset: SeedDataset, name: str) -> list[Any]:
    return list(getattr(dataset, name))


def _csv_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return value


def write_dataset(
    dataset: SeedDataset, out_dir: Path, fmt: str = "json"
) -> list[Path]:
    """Write each entity to ``out_dir`` as JSON, CSV, or both."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for name in ENTITY_NAMES:
        records = _records(dataset, name)
        if fmt in ("json", "both"):
            path = out_dir / f"{name}.json"
            payload = [record.model_dump(mode="json") for record in records]
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            written.append(path)
        if fmt in ("csv", "both"):
            path = out_dir / f"{name}.csv"
            fieldnames = list(type(records[0]).model_fields) if records else []
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for record in records:
                    row = {
                        key: _csv_value(value)
                        for key, value in record.model_dump(mode="python").items()
                    }
                    writer.writerow(row)
            written.append(path)

    manifest = out_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "generated_at": dataset.generated_at.isoformat(),
                "seed": dataset.seed,
                "counts": {name: len(_records(dataset, name)) for name in ENTITY_NAMES},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    written.append(manifest)
    return written


def _parse_anchor(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"expected YYYY-MM-DD, got {value!r}"
        ) from exc
    return parsed.replace(tzinfo=timezone.utc)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.services.data_generator",
        description="Generate synthetic SupplyChainIQ seed data.",
    )
    parser.add_argument(
        "--rows", type=int, default=1000, help="shipment rows to generate (default: 1000)"
    )
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/seed"),
        help="output directory (default: data/seed)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv", "both"),
        default="json",
        help="output format (default: json)",
    )
    parser.add_argument(
        "--anchor",
        type=_parse_anchor,
        default=None,
        help="latest date in the data as YYYY-MM-DD (default: today, UTC)",
    )
    args = parser.parse_args(argv)

    if args.rows < 1:
        parser.error("--rows must be at least 1")

    generator = SupplyChainDataGenerator(seed=args.seed, anchor=args.anchor)
    dataset = generator.generate(rows=args.rows)
    written = write_dataset(dataset, args.out, args.format)

    counts = ", ".join(
        f"{name}={len(_records(dataset, name))}" for name in ENTITY_NAMES
    )
    print(f"seed={args.seed} anchor={generator.anchor.date()} {counts}")
    print(f"wrote {len(written)} files to {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
