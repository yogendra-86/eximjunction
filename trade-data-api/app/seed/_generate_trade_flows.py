"""Generate realistic seed trade flow data.

This produces JSON for trade_flows.json — run once during seed prep.
The numbers are illustrative (loosely based on real-world orders of
magnitude) but should not be quoted as actual statistics.
"""
import json
import random
from pathlib import Path

random.seed(42)

# Realistic top-trade configurations: (hs_code, [reporter, top exporters/partners with relative weights])
# Weights are rough relative magnitudes — actual values are computed below.
TRADE_PROFILES = [
    # Coffee — IN exports to US, DE, IT, BE; imports negligible
    ("090111", "IN", "export", [("US", 1.00), ("DE", 0.85), ("IT", 0.75), ("BE", 0.55), ("RU", 0.45), ("JP", 0.35)], 1.2e9),
    ("090111", "DE", "import",  [("BR", 1.00), ("VN", 0.80), ("CO" if False else "ID", 0.55), ("ID", 0.55), ("IN", 0.40), ("ET" if False else "EG", 0.20)], 3.5e9),
    # Tea — IN export
    ("090230", "IN", "export", [("RU", 1.00), ("AE", 0.65), ("US", 0.50), ("GB", 0.45), ("DE", 0.30)], 8e8),
    # Rice — IN dominates
    ("100630", "IN", "export", [("SA", 1.00), ("AE", 0.85), ("US", 0.40), ("GB", 0.35), ("BD", 0.30), ("ZA", 0.25)], 9.5e9),
    ("100630", "BD", "import",  [("IN", 1.00), ("VN", 0.30), ("TH", 0.25), ("PK", 0.20)], 1.8e9),
    # Wheat — major exporters/importers
    ("100199", "RU", "export", [("EG", 1.00), ("TR", 0.70), ("BD", 0.45), ("ID", 0.40), ("NG", 0.35)], 1.1e10),
    ("100199", "EG", "import",  [("RU", 1.00), ("FR", 0.30), ("AU", 0.25), ("US", 0.20)], 4.0e9),
    # Crude oil — major flows
    ("270900", "IN", "import",  [("RU", 1.00), ("SA", 0.85), ("AE", 0.65), ("US", 0.40), ("NG", 0.25)], 1.4e11),
    ("270900", "SA", "export", [("CN", 1.00), ("JP", 0.75), ("KR", 0.65), ("IN", 0.60), ("US", 0.30)], 1.9e11),
    # Refined petroleum — IN is major exporter
    ("271012", "IN", "export", [("NL", 1.00), ("US", 0.55), ("SG", 0.50), ("AU", 0.40), ("ZA", 0.25)], 4.5e10),
    # Pharmaceuticals — IN, DE, US
    ("300490", "IN", "export", [("US", 1.00), ("GB", 0.35), ("ZA", 0.25), ("RU", 0.20), ("BR", 0.18), ("NG", 0.15)], 1.8e10),
    ("300490", "DE", "export", [("US", 1.00), ("CH", 0.65), ("GB", 0.45), ("FR", 0.40), ("CN", 0.35), ("JP", 0.30)], 8.5e10),
    ("300490", "US", "import",  [("DE", 1.00), ("CH", 0.85), ("IN", 0.55), ("IT", 0.40), ("FR", 0.35)], 1.5e11),
    # Cotton T-shirts — BD, VN, IN export; US, DE, GB import
    ("610910", "BD", "export", [("US", 1.00), ("DE", 0.70), ("GB", 0.45), ("ES", 0.35), ("FR", 0.30)], 6.2e9),
    ("610910", "IN", "export", [("US", 1.00), ("GB", 0.40), ("DE", 0.35), ("AE", 0.25)], 1.8e9),
    ("610910", "US", "import",  [("BD", 1.00), ("VN", 0.85), ("CN", 0.60), ("IN", 0.30)], 1.1e10),
    # Diamonds — IN polishing hub
    ("710231", "IN", "import",  [("RU", 0.55), ("BE", 1.00), ("AE", 0.85), ("ZA", 0.30)], 1.5e10),
    # Gold jewellery — IN export
    ("711319", "IN", "export", [("AE", 1.00), ("US", 0.85), ("SG", 0.40), ("GB", 0.30), ("CA", 0.20)], 1.2e10),
    # Laptops — CN dominant
    ("847130", "CN", "export", [("US", 1.00), ("DE", 0.45), ("JP", 0.35), ("GB", 0.30), ("NL", 0.28), ("IN", 0.20)], 1.6e11),
    ("847130", "IN", "import",  [("CN", 1.00), ("VN", 0.20), ("US", 0.15)], 8e9),
    # Mobile phones — CN, VN export; US, IN, EU import
    ("851712", "CN", "export", [("US", 1.00), ("DE", 0.40), ("JP", 0.30), ("GB", 0.28), ("IN", 0.25), ("KR", 0.22)], 1.4e11),
    ("851712", "VN", "export", [("US", 1.00), ("DE", 0.45), ("KR", 0.40), ("JP", 0.30), ("NL", 0.25)], 5.5e10),
    ("851712", "IN", "import",  [("CN", 1.00), ("VN", 0.55), ("KR", 0.20)], 9e9),
    ("851712", "IN", "export", [("US", 1.00), ("AE", 0.35), ("NL", 0.25), ("GB", 0.20)], 8.5e9),
    # Integrated circuits / processors
    ("854231", "KR", "export", [("CN", 1.00), ("VN", 0.35), ("US", 0.30), ("MY", 0.25), ("JP", 0.20)], 6.0e10),
    ("854231", "CN", "import",  [("KR", 1.00), ("TH", 0.20), ("MY", 0.30), ("JP", 0.25), ("US", 0.20)], 1.2e11),
    # Cars — DE, JP export; US import
    ("870323", "DE", "export", [("US", 1.00), ("CN", 0.85), ("GB", 0.45), ("FR", 0.35), ("IT", 0.30), ("JP", 0.20)], 8.5e10),
    ("870323", "JP", "export", [("US", 1.00), ("CN", 0.40), ("AU", 0.25), ("RU", 0.18), ("SA", 0.15)], 5.5e10),
    ("870323", "US", "import",  [("DE", 1.00), ("JP", 0.95), ("MX", 0.80), ("CA", 0.50), ("KR", 0.45)], 1.7e11),
    # Pepper — IN export
    ("090411", "IN", "export", [("US", 1.00), ("DE", 0.45), ("GB", 0.30), ("CA", 0.20)], 1.5e8),
]

YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

# Year-over-year multipliers to make trends interesting:
#   pandemic dip in 2020, recovery 2021-22, varying 2023-24
YEAR_FACTORS = {
    2019: 0.85,
    2020: 0.72,  # COVID dip
    2021: 0.95,
    2022: 1.10,
    2023: 1.05,
    2024: 1.00,  # base
}

def jitter(x: float, pct: float = 0.08) -> float:
    return x * (1.0 + random.uniform(-pct, pct))


def main():
    out = []
    for hs, reporter, flow, partners, base_total in TRADE_PROFILES:
        # Deduplicate partner list while preserving order/weights
        seen = set()
        uniq = []
        for code, w in partners:
            if code in seen:
                continue
            seen.add(code)
            uniq.append((code, w))

        # normalize weights
        total_w = sum(w for _, w in uniq)
        norm = [(c, w / total_w) for c, w in uniq]

        for year in YEARS:
            year_total = base_total * YEAR_FACTORS[year]
            for partner, weight in norm:
                value = jitter(year_total * weight)
                out.append({
                    "reporter": reporter,
                    "partner": partner,
                    "hs_code": hs,
                    "year": year,
                    "flow_type": flow,
                    "value_usd": round(value, 2),
                    "quantity": None,
                    "quantity_unit": None,
                })

    # write
    path = Path(__file__).parent / "trade_flows.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {len(out)} trade flow rows to {path}")


if __name__ == "__main__":
    main()
