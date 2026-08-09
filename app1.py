import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Trade Calculator App", layout="wide")

# Static rates used to mirror the existing Excel model.
RATES = {
    "brokerage": {"Kotak": {"Delivery": 0.001, "Intraday": 0.0001}, "Zerodha": {"Delivery": 0.0, "Intraday": 0.0001}},
    "stt_buy": {"Kotak": {"Delivery": 0.001, "Intraday": 0.0}, "Zerodha": {"Delivery": 0.001, "Intraday": 0.0}},
    "stt_sell": {"Kotak": {"Delivery": 0.001, "Intraday": 0.00025}, "Zerodha": {"Delivery": 0.001, "Intraday": 0.00025}},
    "stamp_duty": {"Kotak": {"Delivery": 0.00015, "Intraday": 0.00003}, "Zerodha": {"Delivery": 0.00015, "Intraday": 0.00003}},
    "exchange": {"Kotak": {"Delivery": 0.0000307, "Intraday": 0.0000307}, "Zerodha": {"Delivery": 0.0000307, "Intraday": 0.0000307}},
    "sebi": {"Kotak": {"Delivery": 0.000001, "Intraday": 0.000001}, "Zerodha": {"Delivery": 0.000001, "Intraday": 0.000001}},
    "gst": {"Kotak": {"Delivery": 0.18, "Intraday": 0.18}, "Zerodha": {"Delivery": 0.18, "Intraday": 0.18}},
}

columns = [
    "Broker", "Stock / Scrip", "Trade Type", "Funding Type", "Quantity",
    "Purchase Date", "Purchase Price", "Sale Date", "Sale Price",
    "Purchase Value", "Sale Value", "Gross P/L", "Buy Brokerage", "Sell Brokerage",
    "STT - Buy", "STT - Sell", "Stamp Duty", "Exchange Charges", "SEBI Charges",
    "GST", "Total Charges", "Interest Cost", "Net P/L", "Net Return %",
    "Break-even Sale Price"
]

# Build a default DataFrame with correct dtypes
initial_data = []
for i in range(20):
    initial_data.append([
        "Kotak",
        "",
        "Delivery",
        "Margin" if i == 0 else "Cash",
        int(100 if i == 0 else 0),          # Quantity must be int
        date(2026, 7, 9) if i == 0 else None,
        float(1000 if i == 0 else 0),
        None,
        float(1200 if i == 0 else 0),
        # 16 calculated fields (all floats)
        *([0.0] * 16)
    ])

df = pd.DataFrame(initial_data, columns=columns)

# Helper functions.
def compute_row(row):
    broker = row["Broker"]
    trade_type = row["Trade Type"]
    funding_type = row["Funding Type"]
    quantity = int(row["Quantity"]) if row["Quantity"] else 0
    purchase_date = row["Purchase Date"]
    purchase_price = float(row["Purchase Price"]) if row["Purchase Price"] else 0
    sale_date = row["Sale Date"]
    sale_price = float(row["Sale Price"]) if row["Sale Price"] else 0

    purchase_value = quantity * purchase_price
    sale_value = quantity * sale_price
    gross_pl = sale_value - purchase_value

    broker_rate = RATES["brokerage"][broker][trade_type]
    stt_buy_rate = RATES["stt_buy"][broker][trade_type]
    stt_sell_rate = RATES["stt_sell"][broker][trade_type]
    stamp_rate = RATES["stamp_duty"][broker][trade_type]
    exch_rate = RATES["exchange"][broker][trade_type]
    sebi_rate = RATES["sebi"][broker][trade_type]
    gst_rate = RATES["gst"][broker][trade_type]

    buy_brokerage = purchase_value * broker_rate
    sell_brokerage = sale_value * broker_rate
    stt_buy = purchase_value * stt_buy_rate
    stt_sell = sale_value * stt_sell_rate
    stamp_duty = purchase_value * stamp_rate
    exchange_charges = (purchase_value + sale_value) * exch_rate
    sebi_charges = (purchase_value + sale_value) * sebi_rate

    gst = (buy_brokerage + sell_brokerage + exchange_charges + sebi_charges) * gst_rate
    total_charges = buy_brokerage + sell_brokerage + stt_buy + stt_sell + stamp_duty + exchange_charges + sebi_charges + gst

    if funding_type == "Margin" and purchase_date and sale_date:
        days = (sale_date - purchase_date).days
        interest_cost = purchase_value * 0.10 * days / 365 if days > 0 else 0
    elif funding_type == "Margin" and purchase_date:
        days = (date.today() - purchase_date).days
        interest_cost = purchase_value * 0.10 * days / 365 if days > 0 else 0
    else:
        interest_cost = 0

    net_pl = gross_pl - total_charges - interest_cost
    net_return = net_pl / purchase_value if purchase_value else 0

    break_even = ((purchase_value + total_charges + interest_cost) / quantity) if purchase_value > 0 and quantity > 0 else 0

    return {
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
        "Net Return %": net_return,
        "Break-even Sale Price": break_even
    }

st.title("Trade Calculator App")
st.write("Enter values in the yellow input columns. Calculated outputs appear in green columns.")

editable_cols = ["Broker", "Stock / Scrip", "Trade Type", "Funding Type", "Quantity", "Purchase Date", "Purchase Price", "Sale Date", "Sale Price"]
calculated_cols = [col for col in columns if col not in editable_cols]

edited = st.data_editor(
    df,
    key="trade_editor",
    disabled=calculated_cols,
    column_order=columns,
    use_container_width=True
)

# Compute outputs for all rows.
computed = edited.copy()
for idx, row in computed.iterrows():
    calc = compute_row(row)
    for col, value in calc.items():
        computed.at[idx, col] = value

# Display summary metrics.
summary_cols = st.columns(4)
summary_cols[0].metric("Total Trades", int((computed["Quantity"] > 0).sum()))
summary_cols[1].metric("Gross P/L", round(computed["Gross P/L"].sum(), 2))
summary_cols[2].metric("Net P/L", round(computed["Net P/L"].sum(), 2))
summary_cols[3].metric("Win Rate", round((computed["Net P/L"] > 0).sum() / max((computed["Quantity"] > 0).sum(), 1), 3))

# Show the calculated result table beneath the editor.
st.subheader("Calculated Outputs (Green columns in the sheet)")
st.dataframe(computed, use_container_width=True, hide_index=True)
