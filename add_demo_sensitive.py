import pandas as pd

path = "data/raw/mdm_requests.csv"
df = pd.read_csv(path, dtype=str).fillna("")

if any("bank" in c.lower() for c in df.columns):
    print("Already has a bank column, nothing to do.")
else:
    df["bank_account"] = ""
    df["credit_terms"] = ""
    vendors = df["request_type"] == "Vendor"
    customers = df["request_type"] == "Customer"
    df.loc[vendors, "bank_account"] = "DBS 012-345678-9 (demo)"
    df.loc[vendors | customers, "credit_terms"] = "Net 30"
    df.to_csv(path, index=False)
    print("Added bank_account and credit_terms columns.")