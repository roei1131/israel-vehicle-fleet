import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------
st.set_page_config(page_title="Israel Vehicle Fleet", layout="wide")
st.title("Israel's Vehicle Fleet: The Shift to Electric")
st.caption(
    "Source: Ministry of Transport vehicle registry, data.gov.il. "
    "Active registered vehicles only; about 6% of records lack an on-road date "
    "and are excluded."
)


def takeaways(lines):
    """Show a box of conclusions under a chart."""
    st.info("**Key takeaways**\n\n" + "\n".join(f"- {l}" for l in lines))


# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------
by_year = pd.read_csv("by_year.csv")
own = pd.read_csv("by_ownership.csv")
top = pd.read_csv("top_brands.csv")
head = pd.read_csv("headline.csv")

# Brands file: first column = brand, second = count (robust to pandas versions)
top.columns = ["brand", "count"]
top = top.sort_values("count", ascending=False).reset_index(drop=True)

# Ownership file: rename Hebrew columns to English if needed
own = own.rename(columns={"פרטי": "Private", "ליסינג": "Leasing",
                          "חברה": "Company", "השכרה": "Rental"})
own_idx = own.set_index("aliya_year")
own_idx.index = own_idx.index.astype(int)

# Fuel table: rename Hebrew columns to English
by_year = by_year.rename(columns={
    "חשמלי": "electric", "היברידי": "hybrid", "דיזל": "diesel",
    "בנזין": "gasoline", "אחר": "other", "סה״כ": "total",
})

d = by_year.copy()
d["aliya_year"] = d["aliya_year"].astype(int)
d["electrified"] = (d["electric"] + d["hybrid"]) / d["total"] * 100
d["ev_pct"] = d["electric"] / d["total"] * 100
d["hybrid_pct"] = d["hybrid"] / d["total"] * 100
d = d.set_index("aliya_year")

# ---------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------
c1, c2 = st.columns(2)
c1.metric("Private vehicles in registry", f"{int(head['total_private'][0]):,}")
c2.metric("Electric + hybrid share of fleet", f"{head['share_stock'][0]:.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Fuel mix & forecast", "Ownership type", "Top brands", "More forecasts"]
)

# ---------------------------------------------------------------
# Tab 1: electrified share + trend forecast
# ---------------------------------------------------------------
with tab1:
    start = st.selectbox("Forecast based on trend from year",
                         [2020, 2021, 2022, 2023], index=3, key="start_main")
    s, i = np.polyfit(d.loc[start:2026].index.values,
                      d.loc[start:2026, "electrified"].values, 1)
    years_f = np.arange(2027, 2032)
    pred = np.clip(s * years_f + i, 0, 100)
    last = d.loc[2026, "electrified"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(d.index, d["electrified"], marker="o", label="Actual")
    ax.plot(2026, last, marker="o", mfc="white", mec="C0", linestyle="none",
            zorder=5, label="2026 (partial year)")
    ax.plot(np.r_[2026, years_f], np.r_[last, pred], "--", marker="o",
            color="C1", label=f"Linear trend from {start}")
    ax.set_xlabel("Year first on road")
    ax.set_ylabel("% of that year's new vehicles")
    ax.set_title("Share of new private vehicles with electric drive (EV + hybrid)")
    ax.grid(alpha=0.3)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

    jumps = d.loc[2017:2026, "electrified"].diff()
    jump_year = int(jumps.idxmax())
    takeaways([
        f"The electric + hybrid share of new private vehicles rose from "
        f"{d.loc[2020, 'electrified']:.1f}% in 2020 to {last:.1f}% in 2026 "
        "(2026 covers only part of the year).",
        f"The biggest single-year jump was in {jump_year} "
        f"(+{jumps.max():.1f} percentage points).",
        f"Pure EVs peaked at {d['ev_pct'].max():.1f}% of new vehicles in "
        f"{int(d['ev_pct'].idxmax())}. In 2026 pure EVs are {d.loc[2026, 'ev_pct']:.1f}% "
        f"and hybrids {d.loc[2026, 'hybrid_pct']:.1f}%, so hybrids now carry a growing "
        "part of the shift.",
        f"A linear trend from {start} adds about {s:.1f} points per year and reaches "
        f"{pred[-1]:.0f}% in 2031. This is a simple estimate, not a forecast.",
        f"This is the share of NEW registrations. The share of the whole registered "
        f"fleet is much lower ({head['share_stock'][0]:.1f}%), because the fleet "
        "turns over slowly.",
    ])

# ---------------------------------------------------------------
# Tab 2: ownership type
# ---------------------------------------------------------------
with tab2:
    st.line_chart(own_idx)
    st.caption("Share of electric + hybrid among new vehicles, by ownership type.")

    groups_t2 = [g for g in ["Private", "Leasing", "Company"] if g in own_idx.columns]
    lines2 = []
    if len(groups_t2) == 3:
        y_last = int(own_idx.index.max())
        leader = own_idx[groups_t2].idxmax(axis=1)
        priv_years = leader[leader == "Private"].index
        if len(priv_years):
            lines2.append(
                f"Private buyers last had the highest electrified share in "
                f"{int(priv_years.max())}. In {y_last} the leader is {leader.loc[y_last]}."
            )
        lines2.append(
            f"In {y_last}: Company {own_idx.loc[y_last, 'Company']:.1f}%, "
            f"Leasing {own_idx.loc[y_last, 'Leasing']:.1f}%, "
            f"Private {own_idx.loc[y_last, 'Private']:.1f}%."
        )
        lines2.append(
            f"Private moved from {own_idx.loc[2024, 'Private']:.1f}% in 2024 to "
            f"{own_idx.loc[y_last, 'Private']:.1f}% in {y_last}, while Company went from "
            f"{own_idx.loc[2024, 'Company']:.1f}% to {own_idx.loc[y_last, 'Company']:.1f}% "
            f"and Leasing from {own_idx.loc[2024, 'Leasing']:.1f}% to "
            f"{own_idx.loc[y_last, 'Leasing']:.1f}%."
        )
    lines2.append(
        "Possible reading: recent growth is driven more by company and leasing fleets "
        "than by private buyers. The data shows what happened, not why."
    )
    lines2.append(
        "These are shares within each group. Group sizes differ and are not shown here, "
        "so avoid generalizing. Rental is small and noisy."
    )
    takeaways(lines2)

# ---------------------------------------------------------------
# Tab 3: top brands
# ---------------------------------------------------------------
with tab3:
    st.bar_chart(top.set_index("brand")["count"])
    st.caption("Pure EVs registered since 2020, by brand (not by corporate group).")

    CHINESE = {"BYD", "Geely", "XPeng", "MG", "Chery", "Zeekr", "Deepal"}
    is_cn = top["brand"].isin(CHINESE)
    cn_share = top.loc[is_cn, "count"].sum() / top["count"].sum() * 100
    lines3 = [
        f"{top.loc[0, 'brand']} leads with {top.loc[0, 'count']:,} pure EVs since 2020.",
        f"{int(is_cn.sum())} of the top {len(top)} brands are under Chinese ownership "
        f"and account for {cn_share:.0f}% of the top-{len(top)} volume "
        "(MG is historically British but Chinese-owned).",
    ]
    non_cn = top[~is_cn]
    if len(non_cn):
        lines3.append(
            f"The largest non-Chinese brand is {non_cn.iloc[0]['brand']} "
            f"({int(non_cn.iloc[0]['count']):,})."
        )
    lines3.append(
        "Brands are counted separately. Geely and Zeekr, for example, belong to the same "
        "group, so group-level totals would be larger."
    )
    takeaways(lines3)

# ---------------------------------------------------------------
# Tab 4: more forecasts (full years only: up to 2025)
# ---------------------------------------------------------------
with tab4:
    st.subheader("More forecasts")
    st.caption(
        "Simple trend models on new private-vehicle registrations. "
        "Estimates, not predictions. 2026 is a partial year (through Sep), "
        "so it is excluded from the fits."
    )

    full = d.loc[2015:2025].copy()
    full["diesel_pct"] = full["diesel"] / full["total"] * 100
    horizon = np.arange(2026, 2032)

    # ===== 1. New vehicles per year =====
    st.markdown("### 1. New vehicles registered per year")
    FIT_FROM = 2019
    seg = full.loc[FIT_FROM:2025, "total"]
    s_t, i_t = np.polyfit(seg.index.values, seg.values, 1)
    pred_t = np.clip(s_t * horizon + i_t, 0, None)

    fig_a, ax_a = plt.subplots(figsize=(10, 4.5))
    ax_a.plot(full.index, full["total"], marker="o", label="Actual (full years)")
    ax_a.plot(horizon, pred_t, "--", marker="o", color="C1",
              label=f"Linear trend from {FIT_FROM}")
    ax_a.set_ylabel("New vehicles per year")
    ax_a.set_xlabel("Year first on road")
    ax_a.grid(alpha=0.3)
    ax_a.legend()
    st.pyplot(fig_a)
    plt.close(fig_a)

    chg = (full.loc[2025, "total"] / full.loc[FIT_FROM, "total"] - 1) * 100
    takeaways([
        f"New private vehicles per year went from {full.loc[FIT_FROM, 'total']:,.0f} "
        f"in {FIT_FROM} to {full.loc[2025, 'total']:,.0f} in 2025 ({chg:+.0f}%).",
        f"The trend adds about {s_t:,.0f} vehicles per year and reaches roughly "
        f"{pred_t[-1]:,.0f} in 2031.",
        "The fit starts in 2019 and includes the 2020 dip, so the slope is somewhat "
        "inflated by the rebound after it.",
        "Registrations also depend on imports, taxes and the economy, which this "
        "model ignores.",
    ])

    # ===== 2. Diesel share =====
    st.markdown("### 2. Diesel share of new vehicles")
    seg_d = full.loc[2018:2025, "diesel_pct"]
    s_d, i_d = np.polyfit(seg_d.index.values, seg_d.values, 1)
    raw_d = s_d * horizon + i_d
    pred_d = np.clip(raw_d, 0, 100)

    fig_b, ax_b = plt.subplots(figsize=(10, 4.5))
    ax_b.plot(full.index, full["diesel_pct"], marker="o", label="Actual")
    ax_b.plot(horizon, pred_d, "--", marker="o", color="C3",
              label="Linear trend from 2018")
    ax_b.set_ylabel("% of new vehicles")
    ax_b.set_xlabel("Year first on road")
    ax_b.grid(alpha=0.3)
    ax_b.legend()
    st.pyplot(fig_b)
    plt.close(fig_b)

    zero_years = horizon[raw_d <= 0]
    lines_d = [
        f"Diesel fell from {full.loc[2018, 'diesel_pct']:.1f}% of new vehicles in 2018 "
        f"to {full.loc[2025, 'diesel_pct']:.1f}% in 2025.",
        f"In absolute numbers, diesel registrations went from "
        f"{full.loc[2018, 'diesel']:,.0f} to {full.loc[2025, 'diesel']:,.0f} per year, "
        "so this is a real decline and not only a change in share.",
        f"The trend falls about {abs(s_d):.1f} points per year.",
    ]
    if len(zero_years):
        lines_d.append(
            f"The straight line reaches zero in {int(zero_years[0])}. That is a "
            "mechanical result, not a realistic forecast, because a share cannot go "
            "below zero and the decline is likely to slow."
        )
    else:
        lines_d.append(f"The trend still shows {pred_d[-1]:.1f}% diesel in 2031.")
    takeaways(lines_d)

    # ===== 3. Scenarios =====
    st.markdown("### 3. Scenarios: electric + hybrid share of new vehicles")
    target = st.slider("Share reached in 2031 (%)", 40, 90, 60, key="scen_target")
    last25 = d.loc[2025, "electrified"]
    yrs = np.arange(2025, 2032)
    scen_path = np.linspace(last25, target, len(yrs))

    c_s, c_i = np.polyfit(d.loc[2023:2025].index.values,
                          d.loc[2023:2025, "electrified"].values, 1)
    cons = np.clip(c_s * yrs + c_i, 0, 100)
    l_s, l_i = np.polyfit(d.loc[2020:2025].index.values,
                          d.loc[2020:2025, "electrified"].values, 1)
    cont = np.clip(l_s * yrs + l_i, 0, 100)

    fig_c, ax_c = plt.subplots(figsize=(10, 4.5))
    ax_c.plot(d.loc[:2025].index, d.loc[:2025, "electrified"], marker="o", label="Actual")
    ax_c.plot(yrs, cons, "--", color="C2", label="Conservative (trend 2023-2025)")
    ax_c.plot(yrs, cont, "--", color="C1", label="Continued (trend 2020-2025)")
    ax_c.plot(yrs, scen_path, "-", color="C4", linewidth=2.5,
              label=f"Your scenario ({target}% by 2031)")
    ax_c.set_ylabel("% of new vehicles")
    ax_c.set_xlabel("Year first on road")
    ax_c.grid(alpha=0.3)
    ax_c.legend()
    st.pyplot(fig_c)
    plt.close(fig_c)

    need = (target - last25) / (2031 - 2025)
    lines_c = [
        f"The two trend scenarios give roughly {cons[-1]:.0f}% to {cont[-1]:.0f}% "
        "of new vehicles in 2031.",
        f"Reaching {target}% by 2031 requires about {need:.1f} points per year, "
        f"versus {c_s:.1f} in the 2023-2025 trend and {l_s:.1f} in the 2020-2025 trend.",
    ]
    if need > max(c_s, l_s):
        lines_c.append("Your target needs faster growth than either recent trend.")
    elif need < min(c_s, l_s):
        lines_c.append("Your target is slower than both recent trends.")
    else:
        lines_c.append("Your target sits between the two recent trends.")
    takeaways(lines_c)

    # ===== 4. Forecast by ownership type =====
    st.markdown("### 4. Forecast by ownership type")
    st.caption(
        "Electric + hybrid share of new vehicles within each ownership group. "
        "Trend fitted on 2023-2025 (full years); 2026 shown as hollow points. "
        "Rental is excluded because the group is small and noisy."
    )

    own_groups = [g for g in ["Private", "Leasing", "Company"] if g in own_idx.columns]
    yrs_o = np.arange(2025, 2032)
    results = {}

    fig_d, ax_d = plt.subplots(figsize=(10, 4.5))
    for k, g in enumerate(own_groups):
        color = f"C{k}"
        ax_d.plot(own_idx.loc[2020:2025].index, own_idx.loc[2020:2025, g],
                  marker="o", color=color, label=g)
        if 2026 in own_idx.index:
            ax_d.plot(2026, own_idx.loc[2026, g], marker="o", mfc="white",
                      mec=color, linestyle="none", zorder=5)
        fit_seg = own_idx.loc[2023:2025, g]
        s_o, i_o = np.polyfit(fit_seg.index.values, fit_seg.values, 1)
        pred_o = np.clip(s_o * yrs_o + i_o, 0, 100)
        results[g] = (s_o, pred_o)
        ax_d.plot(yrs_o, pred_o, "--", color=color)
    ax_d.set_ylim(0, 100)
    ax_d.set_ylabel("% electric + hybrid")
    ax_d.set_xlabel("Year first on road")
    ax_d.grid(alpha=0.3)
    ax_d.legend(title="Solid = actual, dashed = trend")
    st.pyplot(fig_d)
    plt.close(fig_d)

    lines_o = []
    for g in own_groups:
        s_o, pred_o = results[g]
        cross = yrs_o[pred_o >= 50]
        cross_txt = (f"crosses 50% around {int(cross[0])}" if len(cross)
                     else "does not reach 50% by 2031")
        lines_o.append(
            f"{g}: {own_idx.loc[2025, g]:.1f}% in 2025, trend {s_o:+.1f} points per year, "
            f"about {pred_o[-1]:.0f}% in 2031, {cross_txt}."
        )
    if results:
        best = max(results, key=lambda g: results[g][1][-1])
        lines_o.append(f"{best} has the highest projected share in 2031 under this model.")
    lines_o.append(
        "Each line is fitted on only three data points, so the results are very "
        "sensitive to the chosen window. Treat them as illustrations."
    )
    lines_o.append(
        "Private growth flattened between 2024 and 2025, so a straight line likely "
        "overstates its future. Leasing dipped in 2024 and then rebounded, so its slope "
        "is unstable."
    )
    lines_o.append(
        "These are shares within each group, not vehicle counts. Group sizes differ."
    )
    takeaways(lines_o)
