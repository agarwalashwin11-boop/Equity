import streamlit as st

# ---- Charges & Rates ----
RATES = {
    "KOTAK_DELIVERY": {
        "brokerage_per_leg": 1e-3,
        "stt_buy": 1e-3,
        "stt_sell": 1e-3,
        "stamp_buy": 1.5e-4,
        "exchange_txn": 3.07e-5,
        "sebi": 1e-6,
        "gst": 0.18,
        "dp_charges": 0.0,
    },
    "ZERODHA_DELIVERY": {
        "brokerage_per_leg": 0.0,
        "stt_buy": 1e-3,
        "stt_sell": 1e-3,
        "stamp_buy": 1.5e-4,
        "exchange_txn": 3.07e-5,
        "sebi": 1e-6,
        "gst": 0.18,
        "dp_charges": 0.0,
    }
}

def calc_trade(broker_key, qty, buy_price, sell_price, interest_cost):
    r = RATES[broker_key]

    purchase_value = qty * buy_price
    sale_value = qty * sell_price
    gross_pl = sale_value - purchase_value

    buy_brokerage = purchase_value * r["brokerage_per_leg"]
    sell_brokerage = sale_value * r["brokerage_per_leg"]

    stt_buy = purchase_value * r["stt_buy"]
    stt_sell = sale_value * r["stt_sell"]

    stamp_duty = purchase_value * r["stamp_buy"]

    exch_buy = purchase_value * r["exchange_txn"]
    exch_sell = sale_value * r["exchange_txn"]
    sebi_buy = purchase_value * r["sebi"]
    sebi_sell = sale_value * r["sebi"]

    gst_base = buy_brokerage + sell_brokerage + exch_buy + exch_sell + sebi_buy + sebi_sell
    gst = gst_base * r["gst"]

    dp = r["dp_charges"]

    total_charges = (
        buy_brokerage + sell_brokerage +
        stt_buy + stt_sell +
        stamp_duty +
        exch_buy + exch_sell +
        sebi_buy + sebi_sell +
        gst +
        dp
    )

    net_pl = gross_pl - total_charges - interest_cost
    net_return_pct = (net_pl / purchase_value * 100) if purchase_value != 0 else 0

    break_even_price = (purchase_value + total_charges + interest_cost) / qty

    return {
        "purchase_value": round(purchase_value, 2),
        "sale_value": round(sale_value, 2),
        "gross_pl": round(gross_pl, 2),
        "total_charges": round(total_charges, 2),
        "interest_cost": round(interest_cost, 2),
        "net_pl": round(net_pl, 2),
        "net_return_pct": round(net_return_pct, 2),
        "break_even_price": round(break_even_price, 2),
    }

st.title("Equity Profit Calculator")

broker = st.selectbox("Broker", ["KOTAK_DELIVERY", "ZERODHA_DELIVERY"])
qty = st.number_input("Quantity", min_value=1, step=1)
buy_price = st.number_input("Purchase Price", min_value=0.0, step=0.01)
sell_price = st.number_input("Sale Price", min_value=0.0, step=0.01)
interest = st.number_input("Interest Cost (₹)", min_value=0.0, step=0.01)

if st.button("Calculate"):
    result = calc_trade(broker, qty, buy_price, sell_price, interest)

    st.subheader("Result")
    st.write(f"Purchase Value: ₹{result['purchase_value']}")
    st.write(f"Sale Value: ₹{result['sale_value']}")
    st.write(f"Gross P/L: ₹{result['gross_pl']}")
    st.write(f"Total Charges: ₹{result['total_charges']}")
    st.write(f"Interest Cost: ₹{result['interest_cost']}")
    st.write(f"**Net P/L: ₹{result['net_pl']}**")
    st.write(f"Net Return %: {result['net_return_pct']}%")
    st.write(f"Break-even Sale Price: ₹{result['break_even_price']}")
