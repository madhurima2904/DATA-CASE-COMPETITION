"""Generate the synthetic message data used by the inbox-triage page.

Master data and request history come from the team package in ../data/raw.
This script only creates request_form/data/messages_train.csv (labelled examples),
data/inbox_demo.csv and an empty finance vault. All data is synthetic.
Run once:  python generate_data.py
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)
ROOT = Path(__file__).parent
DATA = ROOT / "data"
RAW = next(p / "data" / "raw" for p in [ROOT, *ROOT.parents] if (p / "data" / "raw" / "customers.csv").exists())
DATA.mkdir(exist_ok=True)

customers = pd.read_csv(RAW / "customers.csv")
items = pd.read_csv(RAW / "items.csv")
known = customers[customers["customer_id"] == customers["canonical_customer_id"]]["customer_name"].tolist()
products = items[items["active_status"] == "Active"]["item_name"].tolist() + ["Product A", "Product B", "Product C"]
new_orgs = ["Penang Heart Centre", "Da Nang Family Hospital", "Surabaya Diagnostic Hub",
            "Chiang Mai Wellness Clinic", "Johor Bahru Specialist Lab"]

templates = {
    "Purchase order": [
        "Please find attached PO {po} for {q} units of {p}. Kindly deliver by {d}.",
        "We would like to order {q} units of {p}. Our PO number is {po}.",
        "Confirming our purchase order {po}: {q} x {p}, delivery to main lab.",
        "Kindly process the attached order for {q} {p} for our monthly replenishment.",
        "PO {po} issued today for {p}, quantity {q}. Please confirm delivery date.",
        "Please supply {q} packs of {p} as per our standing order. Ref {po}.",
        "Order request: {q} {p}, ship to {org}. Purchase order {po} attached.",
    ],
    "Enquiry": [
        "Could you share the price list and lead time for {p}?",
        "Do you carry {p}? We are evaluating suppliers for next year.",
        "What is the shelf life and storage requirement for {p}?",
        "Can you send a quotation for {p} for about {q} units?",
        "We are interested in {p}. Is a product demo available?",
        "Is {p} registered for use in our country? Please send the certificate.",
        "Can you advise the minimum order quantity for {p}?",
    ],
    "Follow-up": [
        "Following up on PO {po}, has it been shipped yet?",
        "Any update on the delivery of {p}? It was due on {d}.",
        "Just checking the status of our earlier order {po}.",
        "We have not received the invoice for {po}. Please resend.",
        "Reminder: still waiting for your reply on the {p} quotation.",
        "Can you confirm the tracking number for order {po}?",
        "Second follow-up on the missing items from {po}.",
    ],
    "MDM setup": [
        "We are a new customer, {org}. Please open an account so we can place orders.",
        "Please set up our hospital {org} in your system before our first PO.",
        "Our company details have changed. Please update our billing address.",
        "Kindly register {org} as a new account; registration documents attached.",
        "We need a customer code for {org} to start purchasing {p}.",
        "Please update our bank details and contact person on your records.",
        "New laboratory {org} opening next month, please create our customer profile.",
    ],
}


def fill(t):
    return t.format(
        po=f"PO{random.randint(10000, 99999)}",
        q=random.choice([5, 10, 20, 30, 50, 100]),
        p=random.choice(products),
        d=(datetime(2026, 11, 1) + timedelta(days=random.randint(0, 40))).strftime("%d %b"),
        org=random.choice(known + new_orgs),
    )


rows = []
for label, ts in templates.items():
    for _ in range(110):
        text = fill(random.choice(ts))
        if random.random() < 0.3:
            text = random.choice(["Hi team, ", "Dear Sir/Madam, ", "Hello, "]) + text
        if random.random() < 0.3:
            text += random.choice([" Thanks.", " Regards, Purchasing.", " Best regards."])
        rows.append((text, label))
random.shuffle(rows)
pd.DataFrame(rows, columns=["text", "label"]).to_csv(DATA / "messages_train.csv", index=False)

inbox = [
    ("Kuala Lumpur Medical Centre 02", "Please process PO55120 for 40 units of B - Lab Consumable 1, delivery next week."),
    ("Penang Heart Centre", "Hello, we would like to order 20 units of A - Diagnostic Reagent 2. PO55871 attached."),
    ("Ho Chi Minh City Medical Centre 02", "Could you send a quotation for C - Diagnostic Device 1, around 5 units?"),
    ("Bangkok University Hospital 08", "Following up on PO54002, has it been shipped yet?"),
    ("Surabaya Diagnostic Hub", "We are a new customer. Please open an account so we can start ordering Product B."),
    ("Singapore General Hospital 01", "Is A - Diagnostic Reagent 3 registered in Singapore? Please send the certificate."),
]
pd.DataFrame(inbox, columns=["sender_org", "text"]).to_csv(DATA / "inbox_demo.csv", index=False)
pd.DataFrame(columns=["request_id", "field", "value"]).to_csv(DATA / "finance_vault.csv", index=False)
print("Synthetic message data written to", DATA)
