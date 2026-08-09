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
input_columns = [
    "Broker", "Stock / Scrip", "Trade Type", "Funding Type",
    "Quantity", "Purchase Date", "Purchase Price", "Sale Date", "Sale Price"
]

calculated_columns = [
    "Purchase Value", "Sale Value", "Gross P/L", "Buy Brokerage", "Sell Brokerage",
    "STT - Buy", "STT - Sell", "Stamp Duty", "Exchange Charges", "SEBI Charges",
    "GST", "Total Charges", "Interest Cost", "Net P/L", "Net Return %",
    "Break-even Sale Price"
]

all_columns = input_columns + calculated_columns

# ============================
# INITIAL 4 ROWS
# ============================
initial_data = []
for i in range(4):
    initial_data.append([
        "Kotak", "", "Delivery", "Cash",
        0, None, 0.0, None, 0.0,
        *([0.0] * len(calculated_columns))
    ])

df = pd.DataFrame(initial_data, columns=all_columns)

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

    return {
        "Purchase Value": round(purchase_value, 2),
        "Sale Value": round(sale_value, 2),
        "Gross P/L": round(gross_pl, 2),
        "Buy Brokerage": round(buy_brokerage, 2),
        "Sell Brokerage": round(sell_brokerage, 2),
        "STT - Buy": round(stt_buy, 2),
        "STT - Sell": round(stt_sell, 2),
        "Stamp Duty": round(stamp_duty, 2),
        "Exchange Charges": round(exchange_charges, 2),
        "SEBI Charges": round(sebi_charges, 2),
        "GST": round(gst, 2),
        "Total Charges": round(total_charges, 2),
        "Interest Cost": round(interest_cost, 2),
        "Net P/L": round(net_pl, 2),
        "Net Return %": round(net_return * 100, 2),
        "Break-even Sale Price": round(break_even, 2)
    }

# ============================
# UI
# ============================
st.title("Trade Calculator App")
st.write("Yellow = Input columns, Green = Calculated columns")

# Column config for input table
column_config_input = {}

for col in ["Broker", "Stock / Scrip", "Trade Type", "Funding Type"]:
    column_config_input[col] = st.column_config.TextColumn(col)

for col in ["Quantity", "Purchase Price", "Sale Price"]:
    column_config_input[col] = st.column_config.NumberColumn(col, format="%.2f")

for col in ["Purchase Date", "Sale Date"]:
    column_config_input[col] = st.column_config.DateColumn(col)

# ============================
# FIRST TABLE (ONLY INPUT COLUMNS)
# ============================
input_df = df[input_columns]

edited = st.data_editor(
    input_df,
    key="trade_editor",
    column_config=column_config_input,
    use_container_width=True,
    hide_index=False
)

# ============================
# COMPUTE OUTPUT
# ============================
computed = edited.copy()

for idx, row in computed.iterrows():
    calc = compute_row(row)
    for col, val in calc.items():
        computed.at[idx, col] = val

# FIX: Index should be 1,2,3,4
computed.index = computed.index + 1

# ============================
# OUTPUT TABLE
# ============================
st.subheader("Calculated Outputs")
st.dataframe(computed, use_container_width=True, hide_index=False)

# ============================
# SUMMARY
# ============================
st.subheader("Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Trades", int((computed["Quantity"] > 0).sum()))
c2.metric("Gross P/L", round(computed["Gross P/L"].sum(), 2))
c3.metric("Net P/L", round(computed["Net P/L"].sum(), 2))
c4.metric("Win Rate", round((computed["Net P/L"] > 0).sum() / max((computed["Quantity"] > 0).sum(), 1), 3))
