from datetime import date
import streamlit as st

st.set_page_config(page_title="Equity Trade – Net Profit Calculator", layout="wide")

# Rates matching the Excel "Charges & Rates" sheet.
RATES = {
    ("Kotak", "Delivery"): {
        "brokerage": 0.001, "stt_buy": 0.001, "stt_sell": 0.001,
        "stamp": 0.00015, "exchange": 0.000031, "sebi": 0.000001, "gst": 0.18,
    },
    ("Kotak", "Intraday"): {
        "brokerage": 0.0001, "stt_buy": 0.0, "stt_sell": 0.00025,
        "stamp": 0.00003, "exchange": 0.000031, "sebi": 0.000001, "gst": 0.18,
    },
    ("Zerodha", "Delivery"): {
        "brokerage": 0.0, "stt_buy": 0.001, "stt_sell": 0.001,
        "stamp": 0.00015, "exchange": 0.0000307, "sebi": 0.000001, "gst": 0.18,
    },
    ("Zerodha", "Intraday"): {
        "brokerage": 0.0001, "stt_buy": 0.0, "stt_sell": 0.00025,
        "stamp": 0.00003, "exchange": 0.0000307, "sebi": 0.000001, "gst": 0.18,
    },
}

OUTPUT_FIELDS = [
    "Purchase Value", "Sale Value", "Gross Profit / (Loss)", "Buy Brokerage",
    "Sell Brokerage", "STT - Buy", "STT - Sell", "Stamp Duty",
    "Exchange Transaction Charges", "SEBI Charges", "GST", "Total Charges",
    "Interest Cost (10% p.a.)", "NET PROFIT / (LOSS)", "Net Return %",
    "Break-even Sale Price",
]

# Styling
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.25rem; max-width: 1500px;}
      .title-band {background:#1f4e78;color:white;padding:14px 18px;border-radius:8px;
                   font-size:25px;font-weight:700;margin-bottom:10px;}
      .hint {color:#555;margin-bottom:14px;}
      .trade-box {background:#fff2cc;border:1px solid #d6b656;
                  padding:14px;border-radius:9px;margin-bottom:10px;}
      .output-card {background:#e2f0d9;border:1px solid #70ad47;border-radius:9px;
                    padding:12px 14px;margin-top:12px;}
      .output-title {font-size:18px;font-weight:700;color:#385723;margin-bottom:6px;}
      .output-row {display:flex;justify-content:space-between;gap:12px;
                   border-bottom:1px solid #c6e0b4;padding:5px 0;}
      .output-row:last-child {border-bottom:none;}
      .output-label {color:#375623;}
      .output-value {font-weight:700;color:#1f3b13;text-align:right;}
    </style>
    """,
    unsafe_allow_html=True,
)

def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}₹{abs(value):,.2f}"

def percent(value: float) -> str:
    return f"{value:.2%}"

def calculate_trade(data: dict) -> dict:
    broker = data["Broker"]
    trade_type = data["Trade Type"]
    funding = data["Funding Type"]
    qty = float(data["Quantity"] or 0)
    buy_price = float(data["Purchase Price"] or 0)
    sell_price = float(data["Sale Price"] or 0)
    purchase_date = data["Purchase Date"]
    sale_date = data["Sale Date"]
    r = RATES[(broker, trade_type)]

    buy_value = qty * buy_price
    sell_value = qty * sell_price
    gross_pl = sell_value - buy_value

    buy_brokerage = buy_value * r["brokerage"]
    sell_brokerage = sell_value * r["brokerage"]
    stt_buy = buy_value * r["stt_buy"]
    stt_sell = sell_value * r["stt_sell"]
    stamp = buy_value * r["stamp"]
    exchange = (buy_value + sell_value) * r["exchange"]
    sebi = (buy_value + sell_value) * r["sebi"]
    gst = (buy_brokerage + sell_brokerage + exchange + sebi) * r["gst"]

    end_date = sale_date or date.today()
    days = max((end_date - purchase_date).days, 0)
    interest = buy_value * 0.10 * days / 365 if funding == "Margin" else 0.0

    transaction_charges = (
        buy_brokerage + sell_brokerage + stt_buy + stt_sell + stamp
        + exchange + sebi + gst
    )
    total_charges = transaction_charges + interest
    net_pl = gross_pl - total_charges
    net_return = net_pl / buy_value if buy_value else 0.0

    be_days = max((date.today() - purchase_date).days, 0)
    be_interest = buy_value * 0.10 * be_days / 365 if funding == "Margin" else 0.0
    buy_costs = buy_value * (r["brokerage"] + r["stt_buy"] + r["stamp"] + r["exchange"] + r["sebi"])
    buy_gst = buy_value * (r["brokerage"] + r["exchange"] + r["sebi"]) * r["gst"]
    sell_cost_rate = r["brokerage"] + r["stt_sell"] + r["exchange"] + r["sebi"]
    sell_gst_rate = (r["brokerage"] + r["exchange"] + r["sebi"]) * r["gst"]
    net_sale_per_share = 1 - sell_cost_rate - sell_gst_rate

    break_even = (
        (buy_value + buy_costs + buy_gst + be_interest) / (qty * net_sale_per_share)
        if qty > 0 and net_sale_per_share > 0 else 0.0
    )

    return {
        "Purchase Value": buy_value,
        "Sale Value": sell_value,
        "Gross Profit / (Loss)": gross_pl,
        "Buy Brokerage": buy_brokerage,
        "Sell Brokerage": sell_brokerage,
        "STT - Buy": stt_buy,
        "STT - Sell": stt_sell,
        "Stamp Duty": stamp,
        "Exchange Transaction Charges": exchange,
        "SEBI Charges": sebi,
        "GST": gst,
        "Total Charges": total_charges,
        "Interest Cost (10% p.a.)": interest,
        "NET PROFIT / (LOSS)": net_pl,
        "Net Return %": net_return,
        "Break-even Sale Price": break_even,
    }

def render_outputs(result: dict):
    rows = []
    for label in OUTPUT_FIELDS:
        value = percent(result[label]) if label == "Net Return %" else money(result[label])
        rows.append(
            f'<div class="output-row"><span class="output-label">{label}</span>'
            f'<span class="output-value">{value}</span></div>'
        )
    st.markdown(
        '<div class="output-card"><div class="output-title">Calculated Outputs</div>'
        + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )

st.markdown('<div class="title-band">EQUITY TRADE – NET PROFIT CALCULATOR</div>', unsafe_allow_html=True)
st.markdown('<div class="hint">All calculations update automatically.</div>', unsafe_allow_html=True)

trade_columns = st.columns(3)
all_results = []

for i, col in enumerate(trade_columns, start=1):
    with col:
        st.markdown(f'<div class="trade-box"><h4>Trade {i}</h4>', unsafe_allow_html=True)

        broker = st.selectbox("Broker", ["Kotak", "Zerodha"], key=f"broker_{i}")
        scrip = st.text_input("Stock / Scrip", key=f"scrip_{i}")
        trade_type = st.selectbox("Trade Type", ["Delivery", "Intraday"], key=f"type_{i}")
        funding = st.selectbox("Funding Type", ["Margin", "Cash"], key=f"funding_{i}")
        quantity = st.number_input("Quantity", min_value=0, step=1, key=f"qty_{i}")
        purchase_date = st.date_input("Purchase Date", key=f"pdate_{i}")
        purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f", key=f"pprice_{i}")

        sale_completed = st.checkbox("Sale completed", key=f"sold_{i}")

        sale_date = st.date_input(
            "Sale Date",
            value=date.today(),
            disabled=not sale_completed,
            key=f"sdate_{i}"
        )

        sale_price = st.number_input(
            "Sale Price",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            disabled=not sale_completed,
            key=f"sprice_{i}"
        )

        payload = {
            "Broker": broker,
            "Stock / Scrip": scrip,
            "Trade Type": trade_type,
            "Funding Type": funding,
            "Quantity": quantity,
            "Purchase Date": purchase_date,
            "Purchase Price": purchase_price,
            "Sale Date": sale_date if sale_completed else None,
            "Sale Price": sale_price if sale_completed else 0.0,
        }

        result = calculate_trade(payload)
        render_outputs(result)
        all_results.append(result)

if all_results:
    st.divider()
    st.subheader("Combined Summary")

    total_purchase = sum(x["Purchase Value"] for x in
