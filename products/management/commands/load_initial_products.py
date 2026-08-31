"""
products/management/commands/load_initial_products.py

One-time data migration: ports the 22-product Rudraksha catalog (originally
compiled into core/knowledge.py) into the database. Run
this once after the products app's migrations are applied.

Safe to re-run: it updates existing rows by product name rather than
duplicating them.

Usage:
    python manage.py load_initial_products
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product, ProductCategory, ProductVariant

# (name, meaning, display_order, [(label, price_or_None), ...])
RUDRAKSHA_BEADS = [
    ("1 Mukhi Sawar Rudraksha",
     "Rarest and most sacred bead, associated with Lord Shiva.", 1,
     [("Small", 365), ("Medium", 699), ("Collector", 915), ("Super Collector", 1131)]),
    ("2 Mukhi Rudraksha",
     "Two natural lines, symbolizes duality and harmony.", 2,
     [("Small", 339), ("Medium", 519), ("Collector", 699), ("Super Collector", 951)]),
    ("3 Mukhi Rudraksha",
     "Three lines, represents sacred fire (Agni), symbolizes transformation.", 3,
     [("Small", 5), ("Medium", 7), ("Collector", 15), ("Super Collector", None)]),
    ("4 Mukhi Rudraksha", "", 4,
     [("Small", 3), ("Medium", 8), ("Collector", 15), ("Super Collector", None)]),
    ("5 Mukhi Rudraksha",
     "The most widely worn Rudraksha; best recommended for meditation and "
     "peace, calms the mind and improves focus.", 5,
     [("Small", 1), ("Medium", 6), ("Collector", 15), ("Super Collector", None)]),
    ("6 Mukhi Rudraksha",
     "Six clefts, symbolizes strength and discipline, associated with Lord Kartikeya.", 6,
     [("Small", 3), ("Medium", 6), ("Collector", 15), ("Super Collector", None)]),
    ("7 Mukhi Rudraksha",
     "Seven lines, symbolizes abundance and grounding energy, associated "
     "with Goddess Mahalakshmi, reflects stability and material balance.", 7,
     [("Small", 19), ("Medium", 33), ("Collector", 51), ("Super Collector", 91)]),
    ("8 Mukhi Rudraksha",
     "Eight divisions, represents Lord Ganesha, symbolizes removal of obstacles.", 8,
     [("Small", 51), ("Medium", 69), ("Collector", 95), ("Super Collector", 159)]),
    ("9 Mukhi Rudraksha",
     "Nine mukhis, for courage and divine protection, helps overcome fears.", 9,
     [("Small", 69), ("Medium", 95), ("Collector", 159), ("Super Collector", 199)]),
    ("10 Mukhi Rudraksha",
     "Ten clefts, associated with Lord Vishnu, represents harmony, "
     "stability, and protection from negative influences.", 10,
     [("Small", 51), ("Medium", 69), ("Collector", 95), ("Super Collector", 159)]),
    ("11 Mukhi Rudraksha",
     "Eleven lines representing the eleven Rudras, powerful manifestations of Shiva.", 11,
     [("Small", 95), ("Medium", 159), ("Collector", 199), ("Super Collector", None)]),
    ("12 Mukhi Rudraksha",
     "Twelve divisions, associated with Lord Surya (the Sun God).", 12,
     [("Small", 95), ("Medium", 159), ("Collector", 199), ("Super Collector", None)]),
    ("13 Mukhi Rudraksha", "", 13,
     [("Small", 159), ("Medium", 199), ("Collector", 339), ("Super Collector", None)]),
    ("14 Mukhi Rudraksha",
     "Fourteen clefts, traditionally associated with Lord Hanuman.", 14,
     [("Small", 319), ("Medium", 699), ("Collector", 951), ("Super Collector", None)]),
    ("15 Mukhi Rudraksha", "", 15,
     [("Small", 339), ("Medium", 519), ("Collector", 951), ("Super Collector", 1599)]),
    ("16 Mukhi Rudraksha", "", 16,
     [("Small", 699), ("Medium", 951), ("Collector", 1599), ("Super Collector", None)]),
    ("18 Mukhi Rudraksha", "", 18,
     [("Small", 3195), ("Medium", 3300), ("Collector", 5100), ("Super Collector", None)]),
    ("19 Mukhi Rudraksha",
     "Rare and revered bead, nineteen naturally formed mukhis.", 19,
     [("Small", 5199), ("Medium", 9159), ("Collector", 13995), ("Super Collector", None)]),
    ("21 Mukhi Rudraksha",
     "One of the rarest and most powerful Rudraksha beads.", 21,
     [("Medium", None)]),
    ("Gauri Shankar Rudraksha", "", 100,
     [("Small", 95), ("Medium", 159), ("Collector", 199), ("Super Collector", None)]),
]

RUDRAKSHA_BRACELETS = [
    ("5 Mukhi Rudraksha Bracelet",
     "Lord Shiva's bead; promotes health, prosperity, protection, focus, "
     "willpower, and confidence.", 1,
     [("Standard", 50)]),
]

SIDDHA_MALA = [
    ("Siddha Mala",
     "A comprehensive spiritual mala combining 1 to 14 Mukhi beads with "
     "Gauri Shankar and Ganesha Rudraksha; a sacred choice for serious practitioners.", 1,
     [("Standard", 1000)]),
]

CATEGORIES = {
    "Rudraksha Beads": RUDRAKSHA_BEADS,
    "Rudraksha Bracelets": RUDRAKSHA_BRACELETS,
    "Siddha Mala": SIDDHA_MALA,
}


class Command(BaseCommand):
    help = "Loads the initial Rudrantra product catalog into the database."

    @transaction.atomic
    def handle(self, *args, **options):
        total_products = 0
        total_variants = 0

        for category_name, products in CATEGORIES.items():
            category, _ = ProductCategory.objects.get_or_create(name=category_name)

            for name, meaning, display_order, variants in products:
                product, created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        "category": category,
                        "meaning": meaning,
                        "display_order": display_order,
                    },
                )
                if not created:
                    product.category = category
                    product.meaning = meaning
                    product.display_order = display_order
                    product.save()
                    product.variants.all().delete()

                for label, price in variants:
                    ProductVariant.objects.create(
                        product=product, label=label, price=price
                    )
                    total_variants += 1

                total_products += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {total_products} products with {total_variants} variants "
                f"across {len(CATEGORIES)} categories."
            )
        )