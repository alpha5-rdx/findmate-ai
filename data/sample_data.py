"""Small demo dataset: the same item described with different words."""
from datetime import date, timedelta

from ai.matcher import ensure_embeddings, run_matching
from database import db

_T = date.today()


def _d(days):
    return _T - timedelta(days=days)


# (kind, name, description, category, location, days_ago, contact_name, email)
SAMPLES = [
    # --- pair 1: wallet
    ("lost", "Black leather wallet", "Slim black leather wallet with several bank cards, a student ID and some cash inside.",
     "Wallets & Bags", "Central Library", 5, "Sara Khan", "sara@example.com"),
    ("found", "Dark billfold", "Small dark-coloured leather billfold holding credit cards and a university identity card.",
     "Wallets & Bags", "Main Library reading hall", 4, "Tom Reed", "tom@example.com"),
    # --- pair 2: phone
    ("lost", "iPhone 13", "Blue iPhone 13 in a clear case with a cracked screen corner.",
     "Electronics", "Bus Station", 3, "Omar Ali", "omar@example.com"),
    ("found", "Apple smartphone", "Found a damaged Apple mobile phone, navy colour, transparent cover, screen is shattered at the edge.",
     "Electronics", "City Bus Terminal", 2, "Lina Park", "lina@example.com"),
    # --- pair 3: keys
    ("lost", "Car keys", "Toyota car key fob with a red leather keychain and two small house keys.",
     "Keys", "Supermarket parking lot", 6, "Daniel Cruz", "daniel@example.com"),
    ("found", "Set of keys", "A bunch of keys with a Toyota remote and a scarlet leather tag, found on the ground.",
     "Keys", "Grocery store car park", 5, "Mia Chen", "mia@example.com"),
    # --- pair 4: backpack
    ("lost", "Grey backpack", "Grey Nike backpack containing a laptop, notebooks and a water bottle.",
     "Wallets & Bags", "Engineering Building", 2, "Hana Yusuf", "hana@example.com"),
    ("found", "Gray rucksack", "Charcoal Nike rucksack with textbooks, a notebook computer and a drink bottle inside.",
     "Wallets & Bags", "Engineering Faculty hallway", 1, "Ben Wright", "ben@example.com"),
    # --- unmatched distractors
    ("lost", "Silver bracelet", "Thin silver bracelet with a tiny heart charm, sentimental gift.",
     "Jewelry", "City Park", 7, "Ivy Moore", "ivy@example.com"),
    ("found", "Green umbrella", "Large green umbrella with a wooden handle left at the cafe.",
     "Clothing & Accessories", "Corner Cafe", 1, "Sam Lee", "sam@example.com"),
]


def load_samples() -> int:
    """Insert the sample reports (once) and run the matching engine."""
    if db.count_items() > 0:
        return 0
    for n, (kind, name, desc, cat, loc, days, cname, email) in enumerate(SAMPLES, 1):
        db.add_item(kind, name, desc, cat, loc, _d(days), None, cname, email, None,
                    contact_number=f"0300000{n:04d}")
    ensure_embeddings(db.list_items())
    run_matching()
    return len(SAMPLES)
