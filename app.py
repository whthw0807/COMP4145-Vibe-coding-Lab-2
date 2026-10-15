import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import streamlit as st

from trading_strategy import (
    calculate_moving_averages,
    get_stock_data,
    identify_golden_cross,
    implement_strategy,
)


st.set_page_config(page_title="MSFT Trading Dashboard", layout="wide")


@st.cache_data
def load_analysis():
    data = get_stock_data("MSFT")
    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions


def summarize_trades(positions):
    if positions.empty:
        return {
            "Total trades": 0,
            "Winning trades": 0,
            "Losing trades": 0,
            "Win rate": 0.0,
            "Average profit (%)": 0.0,
            "Average holding days": 0.0,
            "Best trade (%)": 0.0,
            "Worst trade (%)": 0.0,
        }

    win_trades = int((positions["ProfitPct"] > 0).sum())
    loss_trades = int((positions["ProfitPct"] <= 0).sum())
    total_trades = len(positions)

    summary = {
        "Total trades": total_trades,
        "Winning trades": win_trades,
        "Losing trades": loss_trades,
        "Win rate": round((win_trades / total_trades) * 100, 2) if total_trades else 0.0,
        "Average profit (%)": round(float(positions["ProfitPct"].mean()), 2),
        "Average holding days": round(float(positions["HoldingDays"].mean()), 2),
        "Best trade (%)": round(float(positions["ProfitPct"].max()), 2),
        "Worst trade (%)": round(float(positions["ProfitPct"].min()), 2),
    }
    return summary


def render_price_chart(data, positions):
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(data.index, data["Close"], label="Price", color="navy", linewidth=2)
    ax.plot(data.index, data["MA50"], label="50-day MA", color="orange", linewidth=1.5)
    ax.plot(data.index, data["MA200"], label="200-day MA", color="red", linewidth=1.5)

    if not positions.empty:
        for _, trade in positions.iterrows():
            ax.scatter(trade["BuyDate"], trade["BuyPrice"], color="green", s=50, label="Buy" if "Buy" not in ax.get_legend_handles_labels()[1] else "")
            ax.scatter(trade["SellDate"], trade["SellPrice"], color="red", s=50, label="Sell" if "Sell" not in ax.get_legend_handles_labels()[1] else "")

    ax.set_title("MSFT Price Trend with Moving Averages")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    st.pyplot(fig)


page = st.sidebar.radio(
    "Navigation",
    ["Price Chart", "Trade Statistics", "Detailed Trades"],
    index=0,
)


data, positions = load_analysis()
summary = summarize_trades(positions)

if page == "Price Chart":
    st.title("Price Chart")
    st.caption("MSFT stock price across the full period with moving averages and trade signals")
    render_price_chart(data, positions)

elif page == "Trade Statistics":
    st.title("Trade Statistics")
    st.caption("Overall summary of all implemented trades")

    cols = st.columns(4)
    metrics = [
        ("Total trades", summary["Total trades"]),
        ("Winning trades", summary["Winning trades"]),
        ("Losing trades", summary["Losing trades"]),
        ("Win rate (%)", summary["Win rate"]),
    ]

    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average profit (%)", summary["Average profit (%)"])
    c2.metric("Average holding days", summary["Average holding days"])
    c3.metric("Best trade (%)", summary["Best trade (%)"])
    c4.metric("Worst trade (%)", summary["Worst trade (%)"])

    if not positions.empty:
        st.bar_chart(positions.set_index("BuyDate")["ProfitPct"].sort_index())

elif page == "Detailed Trades":
    st.title("Detailed Trades")
    st.caption("Record of each trade including entry, exit, holding period, and profit")

    if positions.empty:
        st.info("No trades were detected for the selected strategy.")
    else:
        display_df = positions.copy()
        display_df["BuyDate"] = display_df["BuyDate"].dt.strftime("%Y-%m-%d")
        display_df["SellDate"] = display_df["SellDate"].dt.strftime("%Y-%m-%d")
        display_df["ProfitPct"] = display_df["ProfitPct"].round(2)
        st.dataframe(display_df, use_container_width=True)


if positions.empty:
    st.warning("No trading signals were generated based on the current golden cross strategy.")
