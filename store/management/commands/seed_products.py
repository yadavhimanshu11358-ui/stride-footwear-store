import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from store.models import Product, Review


CATEGORY_TEMPLATES = [
    {
        "category": "running",
        "label": "Running Shoe",
        "brand": "Stride Performance",
        "base_price": 1199,
        "step_price": 25,
        "sizes": ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10"],
        "images": [
            "[https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1460353581641-37baddab0fa2?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1460353581641-37baddab0fa2?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?auto=format&fit=crop&w=900&q=85)",
        ],
        "desc": "Breathable mesh upper with high-rebound cushioned sole for running, gym, and daily walks.",
        "review": "Super light on feet and great shock absorption during morning runs.",
    },
    {
        "category": "sneakers",
        "label": "Street Sneaker",
        "brand": "Stride Street",
        "base_price": 1399,
        "step_price": 30,
        "sizes": ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10"],
        "images": [
            "[https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=900&q=85)",
        ],
        "desc": "Clean modern street sneaker with soft memory-foam insole and durable grip outsole.",
        "review": "Looks sharp with denim and joggers; soft insole even after hours out.",
    },
    {
        "category": "casual",
        "label": "Casual Shoe",
        "brand": "Stride Daily",
        "base_price": 899,
        "step_price": 20,
        "sizes": ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10"],
        "images": [
            "[https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1560769629-975ec13e6d6d?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1560769629-975ec13e6d6d?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1579338559194-a162d19bf842?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1579338559194-a162d19bf842?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?auto=format&fit=crop&w=900&q=85)",
        ],
        "desc": "Flexible everyday casual shoe designed for college, outings, and effortless comfort.",
        "review": "Easy slip-on comfort and solid stitching for everyday college and travel.",
    },
    {
        "category": "slippers",
        "label": "Daily Chappal",
        "brand": "Stride Comfort",
        "base_price": 299,
        "step_price": 15,
        "sizes": ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10"],
        "images": [
            "[https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1595341888016-a392ef81b7de?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1595341888016-a392ef81b7de?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=900&q=85)",
        ],
        "desc": "Soft cushioned footbed chappal with anti-slip grip for comfortable home and daily use.",
        "review": "Very soft footbed for heel comfort and reliable grip on smooth floors.",
    },
    {
        "category": "sandals",
        "label": "Outdoor Sandal",
        "brand": "Stride Rugged",
        "base_price": 699,
        "step_price": 20,
        "sizes": ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10"],
        "images": [
            "[https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1595341888016-a392ef81b7de?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1595341888016-a392ef81b7de?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=85)",
        ],
        "desc": "Adjustable strap sandal with sturdy outsole built for travel, monsoon, and daily wear.",
        "review": "Straps hold securely without pinching and sole handles rough roads well.",
    },
    {
        "category": "formal",
        "label": "Formal Shoe",
        "brand": "Stride Formals",
        "base_price": 1599,
        "step_price": 35,
        "sizes": ["UK 7", "UK 8", "UK 9", "UK 10"],
        "images": [
            "[https://images.unsplash.com/photo-1614252369475-531eba835eb1?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1614252369475-531eba835eb1?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1533867617858-e7b97e060509?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1533867617858-e7b97e060509?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1449505278894-297fdb3edbc1?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1449505278894-297fdb3edbc1?auto=format&fit=crop&w=900&q=85)",
            "[https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=900&q=85](https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=900&q=85)",
        ],
        "desc": "Refined formal shoe with padded insole and flexible sole for office and formal wear.",
        "review": "Clean finish for office meetings and much softer inside than regular formals.",
    },
]

EDITIONS = [
    "Aero", "Prime", "Lite", "Max", "Flex", "Pro", "Core", "Edge", "Pulse", "Glide",
    "Swift", "Volt", "Craft", "Nova", "Drift", "Trek", "Wave", "Pace", "Bold", "Classic",
]

SAMPLE_BUYERS = ["Aarav Sharma", "Priya Nair", "Vikram Joshi", "Ananya Verma", "Karan Malhotra"]


class Command(BaseCommand):
    help = "Creates at least 50 products in every footwear category (300 total) with size stock"

    def add_arguments(self, parser):
        parser.add_argument("--per-category", type=int, default=50)

    def handle(self, *args, **options):
        per_cat = max(50, options["per_category"])
        created_total = 0

        for cat_cfg in CATEGORY_TEMPLATES:
            for i in range(1, per_cat + 1):
                ed = EDITIONS[(i - 1) % len(EDITIONS)]
                name = f"Stride {ed} {cat_cfg['label']} #{i:02d}"
                price_val = cat_cfg["base_price"] + ((i - 1) % 12) * cat_cfg["step_price"]
                mrp_val = int(price_val * 1.55)
                img_url = cat_cfg["images"][(i - 1) % len(cat_cfg["images"])]

                size_map = {}
                for s_idx, sz in enumerate(cat_cfg["sizes"]):
                    if (i + s_idx) % 7 == 0:
                        size_map[sz] = 0
                    else:
                        size_map[sz] = 2 + ((i + s_idx) % 6)

                product, created = Product.objects.update_or_create(
                    name=name,
                    defaults={
                        "brand_tag": cat_cfg["brand"],
                        "category": cat_cfg["category"],
                        "price": Decimal(f"{price_val}.00"),
                        "original_price": Decimal(f"{mrp_val}.00"),
                        "sizes": ", ".join(cat_cfg["sizes"]),
                        "size_stock_json": json.dumps(size_map),
                        "stock": sum(size_map.values()),
                        "is_featured": i <= 4,
                        "description": f"{name} — {cat_cfg['desc']}",
                        "image": None,
                        "image_url": img_url,
                    },
                )
                if created:
                    created_total += 1
                    Review.objects.create(
                        product=product,
                        reviewer_name=SAMPLE_BUYERS[(i - 1) % len(SAMPLE_BUYERS)],
                        fit_feedback="True to Size",
                        rating=5 if i % 2 == 0 else 4,
                        comment=cat_cfg["review"],
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! {per_cat} products in each of the 6 categories ({per_cat * 6} total). New added: {created_total}."
            )
        )