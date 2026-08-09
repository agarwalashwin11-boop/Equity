import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Trade Calculator App", layout="wide")

# ============================
# BROKERAGE RATE TABLE
# ============================
RATES = {
    "brokerage": {"Kotak": {"Delivery": 0.001, "Intraday": 0.0001}, "Zerodha": {"Delivery": 0.0, "Intraday": 0.0001}},
    "stt_buy": {"Kotak": {"Delivery": 0.001, "Intraday": 0.0}, "Zerodha": {"Delivery": 0.001, "Intraday": 0.0}},
    "stt_sell": {"Kotak": {"Delivery": 0.001, "Intraday": 0.00025}, "Zerodha": {"Delivery": 0.001, "Intraday": 0.00025}},
    "stamp_duty": {"Kotak": {"Delivery": 0.00015, "Intraday": 0.00003}, "Zerodha": {"Delivery": 0.00015, "Intraday": 0.00003}},
    "exchange": {"Kotak": {"Delivery": 0.0000307, "Intraday": 0.0000307}, "Zerodha": {"Delivery": 0.0000307, "Intraday": 0.0000307}},
    "sebi": {"Kotak": {"Delivery": 0.000001, "Intraday": 0.000001}, "Zerodha": {"Delivery": 0.000001, "Intraday": 0.000001}},
    "gst": {"Kotak": {"Delivery": 0.18, "Intraday": 0.18}, "Zerodha": {"Delivery": 0.18, "Intraday": 0.18}},
}

# ============================
# COLUMN DEFINITIONS
# ============================
columns = [
    "Broker", "Stock / Scrip", "Trade Type", "Funding Type", "Quantity",
    "Purchase Date", "Purchase Price", "Sale Date", "Sale Price",
    "Purchase Value", "Sale Value", "Gross P/L", "Buy Brokerage", "Sell Brokerage",
    "STT - Buy", "STT - Sell", "Stamp Duty", "Exchange Charges", "SEBI Charges",
    "GST", "Total Charges", "Interest Cost", "Net P/L", "Net Return %",
    "Break-even Sale Price"
]

editable_cols = [
    "Broker", "Stock / Scrip", "Trade Type", "Funding Type",
    "Quantity", "Purchase Date", "Purchase Price", "Sale Date", "Sale Price"
]

calculated_cols = [c for c in columns if c not in editable_cols]

# ============================
# INITIAL 4 ROWS
# ============================
initial_data = []
for i in range(4):
    initial_data.append([
        "Kotak",
        "",
        "Delivery",
        "Cash",
        0,
        None,
        0.0,
        None,
        0.0,
        *([0.0] * 16)
    ])

df = pd.DataFrame(initial_data, columns=columns)

# ============================
# CALCULATION LOGIC
# ============================
def compute_row(row):
    broker = row["Broker"]
    trade_type = row["Trade Type"]
    funding_type = row["Funding Type"]

    qty = int(row["Quantity"]) if row["Quantity"] else 0
    buy_price = float(row["Purchase Price"]) if row["Purchase Price"] else 0
    sell_price = float(row["Sale Price"]) if row["Sale Price"] else 0

    purchase_date = row["Purchase Date"]
    sale_date = row["Sale Date"]

    purchase_value = qty * buy_price
    sale_value = qty * sell_price
    gross_pl = sale_value - purchase_value

    # Rates
    br = RATES["brokerage"][broker][trade_type]
    stt_b = RATES["stt_buy"][broker][trade_type]
    stt_s = RATES["stt_sell"][broker][trade_type]
    stamp = RATES["stamp_duty"][broker][trade_type]
    exch = RATES["exchange"][broker][trade_type]
    sebi = RATES["sebi"][broker][trade_type]
    gst_rate = RATES["gst"][broker][trade_type]

    buy_brokerage = purchase_value * br
    sell_brokerage = sale_value * br
    stt_buy = purchase_value * stt_b
    stt_sell = sale_value * stt_s
    stamp_duty = purchase_value * stamp
    exchange_charges = (purchase_value + sale_value) * exch
    sebi_charges = (purchase_value + sale_value) * sebi

    gst = (buy_brokerage + sell_brokerage + exchange_charges + sebi_charges) * gst_rate
    total_charges = buy_brokerage + sell_brokerage + stt_buy + stt_sell + stamp_duty + exchange_charges + sebi_charges + gst

    # Interest
    if funding_type == "Margin" and purchase_date:
        if sale_date:
            days = (sale_date - purchase_date).days
        else:
            days = (date.today() - purchase_date).days
        interest_cost = purchase_value * 0.10 * days / 365 if days > 0 else 0
    else:
        interest_cost = 0

    net_pl = gross_pl - total_charges - interest_cost
    net_return = (net_pl / purchase_value) if purchase_value else 0

    break_even = ((purchase_value + total_charges + interest_cost) / qty) if qty > 0 else 0

    # Round everything to 2 decimals
    return {k: round(v, 2) for k, v in {
        "Purchase Value": purchase_value,
        "Sale Value": sale_value,
        "Gross P/L": gross_pl,
        "Buy Brokerage": buy_brokerage,
        "Sell Brokerage": sell_brokerage,
        "STT - Buy": stt_buy,
        "STT - Sell": stt_sell,
        "Stamp Duty": stamp_duty,
        "Exchange Charges": exchange_charges,
        "SEBI Charges": sebi_charges,
        "GST": gst,
        "Total Charges": total_charges,
        "Interest Cost": interest_cost,
        "Net P/L": net_pl,
        "Net Return %": net_return * 100,
        "Break-even Sale Price": break_even
    }.items()}

# ============================
# UI
# ============================
st.title("Trade Calculator App")
st.write("Yellow = Input columns, Green = Calculated columns")

edited = st.data_editor(
    df,
    key="trade_editor",
    use_container_width=True
)

# ============================
# COMPUTE ALL ROWS
# ============================
computed = edited.copy()

for idx, row in computed.iterrows():
    calc = compute_row(row)
    for col, val in calc.items():
        computed.at[idx, col] = val

# ============================
# COLOR STYLING (OUTPUT ONLY)
# ============================
def highlight_cells(val, col):
    if col in editable_cols:
        return "background-color: #FFFACD"  # Yellow
    else:
        return "background-color: #DFFFD6"  # Green

styled = computed.style.apply(
    lambda row: [highlight_cells(row[col], col) for col in computed.columns],
    axis=1
).format("{:.2f}")

# ============================
# SUMMARY
# ============================
st.subheader("Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Trades", int((computed["Quantity"] > 0).sum()))
c2.metric("Gross P/L", round(computed["Gross P/L"].sum(), 2))
c3.metric("Net P/L", round(computed["Net P/L"].sum(), 2))
c4.metric("Win Rate", round((computed["Net P/L"] > 0).sum() / max((computed["Quantity"] > 0).sum(), 1), 3))

# ============================
# OUTPUT TABLE
# ============================
st.subheader("Calculated Outputs (Colored)")
st.dataframe(styled, use_container_width=True)
