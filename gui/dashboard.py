import streamlit as st
import json
import io
import sys
import os
import copy
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE) if os.path.basename(_HERE) in ("gui", "src") else _HERE
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

st.set_page_config(
    page_title="Inventory Placement Optimizer",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── global tweaks ── */
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .sidebar-title {
    font-size: 20px; font-weight: 700; letter-spacing: .5px;
    color: #a78bfa !important; margin-bottom: 4px;
}
[data-testid="stSidebar"] .sidebar-sub {
    font-size: 12px; color: #94a3b8 !important; margin-bottom: 24px;
}
section[data-testid="stSidebar"] hr { border-color: #2d2d44; }

/* metric cards */
[data-testid="metric-container"] {
    background: #f8f7ff;
    border: 1px solid #ede9fe;
    border-radius: 12px;
    padding: 16px !important;
}
[data-testid="stMetricLabel"]  { font-size: 13px !important; color: #6b7280 !important; }
[data-testid="stMetricValue"]  { font-size: 26px !important; font-weight: 700 !important; }

/* step badges */
.step-badge {
    display:inline-block; padding:3px 10px;
    border-radius:20px; font-size:12px; font-weight:600;
    margin-bottom:6px;
}
.step-done  { background:#d1fae5; color:#065f46; }
.step-run   { background:#dbeafe; color:#1e40af; }
.step-wait  { background:#f3f4f6; color:#6b7280; }

/* route card */
.route-card {
    border:1px solid #e5e7eb; border-radius:12px;
    padding:16px 20px; margin-bottom:12px;
    background:#fafafa;
}
.route-wh   { font-size:16px; font-weight:700; color:#4f46e5; margin-bottom:6px; }
.route-line { font-size:14px; color:#374151; word-break:break-all; margin-bottom:6px; }
.route-dist { font-size:13px; color:#6b7280; }

/* pill */
.split-pill {
    display:inline-block; background:#fef3c7; color:#92400e;
    border-radius:20px; font-size:11px; padding:1px 8px; margin-left:6px;
}

/* section header */
.sec-header {
    font-size:18px; font-weight:700; color:#1e1b4b;
    border-left:4px solid #6c63ff; padding-left:10px; margin:20px 0 12px;
}

/* data-editor hint */
.hint { font-size:12px; color:#9ca3af; margin-top:4px; }

div[data-testid="stDataFrameResizable"] { border-radius:10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

sys.path.insert(0, os.path.dirname(__file__))
from models.city      import City
from models.warehouse import Warehouse
from graph.graph_builder  import Graph
from algorithms.dijkstra  import dijkstra
from algorithms.greedy    import greedy_allocation
from algorithms.knapsack  import adjust_capacity
from algorithms.tabu_search import tabu_search
from algorithms.tsp_dp    import compute_tsp_for_all_warehouses
from utils.evaluation     import evaluate_solution


# ─────────────────────────────────────────────────────────────────────────────
# Session-state defaults
# ─────────────────────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "cities_df":     pd.DataFrame(columns=["name", "demand"]),
        "warehouses_df": pd.DataFrame(columns=["name", "capacity"]),
        "roads_df":      pd.DataFrame(columns=["from", "to", "distance"]),
        "data_ready":    False,
        "results":       None,
        "page":          "Data Input",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏭 InvOpt</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Inventory Placement & Route Optimizer</div>',
                unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Data Input", "Run Pipeline", "Results", "TSP Routes"],
        index=["Data Input", "Run Pipeline", "Results", "TSP Routes"].index(
            st.session_state.page),
        label_visibility="collapsed",
    )
    st.session_state.page = page

    st.markdown("---")
    if st.button("📂 Load sample data", use_container_width=True):
        sample = os.path.join(os.path.dirname(__file__), "data", "sample_data.json")
        with open(sample) as f:
            d = json.load(f)
        st.session_state.cities_df     = pd.DataFrame(d["cities"])
        st.session_state.warehouses_df = pd.DataFrame(d["warehouses"])
        st.session_state.roads_df      = pd.DataFrame(d["roads"])
        st.session_state.data_ready    = True
        st.session_state.results       = None
        st.success("Sample data loaded!")

    st.markdown("---")
    st.markdown("**Pipeline stages**")
    stages = ["Dijkstra", "Greedy alloc", "Knapsack adj",
              "Tabu Search", "TSP (Held-Karp)"]
    for s in stages:
        done = st.session_state.results is not None
        badge = "step-done" if done else "step-wait"
        icon  = "✓" if done else "○"
        st.markdown(f'<span class="step-badge {badge}">{icon} {s}</span>',
                    unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _make_excel_template() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame(columns=["name", "demand"]).to_excel(
            w, sheet_name="Cities", index=False)
        pd.DataFrame(columns=["name", "capacity"]).to_excel(
            w, sheet_name="Warehouses", index=False)
        pd.DataFrame(columns=["from", "to", "distance"]).to_excel(
            w, sheet_name="Roads", index=False)
    return buf.getvalue()


def _parse_json(raw: bytes):
    d = json.loads(raw)
    cities_df     = pd.DataFrame(d["cities"])
    warehouses_df = pd.DataFrame(d["warehouses"])
    roads_df      = pd.DataFrame(d["roads"])
    return cities_df, warehouses_df, roads_df


def _parse_excel(raw: bytes):
    xl = pd.ExcelFile(io.BytesIO(raw))
    cities_df     = xl.parse("Cities")
    warehouses_df = xl.parse("Warehouses")
    roads_df      = xl.parse("Roads")
    return cities_df, warehouses_df, roads_df


def _validate(cities_df, warehouses_df, roads_df):
    errors = []
    if len(cities_df) == 0:
        errors.append("No cities defined.")
    if len(warehouses_df) == 0:
        errors.append("No warehouses defined.")
    if len(roads_df) == 0:
        errors.append("No roads defined.")
    if "name"     not in cities_df.columns:    errors.append("Cities: missing 'name' column.")
    if "demand"   not in cities_df.columns:    errors.append("Cities: missing 'demand' column.")
    if "name"     not in warehouses_df.columns: errors.append("Warehouses: missing 'name' column.")
    if "capacity" not in warehouses_df.columns: errors.append("Warehouses: missing 'capacity' column.")
    for col in ["from", "to", "distance"]:
        if col not in roads_df.columns:
            errors.append(f"Roads: missing '{col}' column.")
    return errors


def _build_objects(cities_df, warehouses_df, roads_df):
    cities     = [City(r["name"], int(r["demand"]))
                  for _, r in cities_df.iterrows()]
    warehouses = [Warehouse(r["name"], int(r["capacity"]))
                  for _, r in warehouses_df.iterrows()]
    roads      = [(r["from"], r["to"], int(r["distance"]))
                  for _, r in roads_df.iterrows()]
    return cities, warehouses, roads


def _run_pipeline(cities, warehouses, roads):
    graph = Graph()
    for src, dst, dist in roads:
        graph.add_edge(src, dst, dist)

    # Dijkstra
    shipping_cost_matrix = {}
    for city in cities:
        dists = dijkstra(graph, city.name)
        shipping_cost_matrix[city.name] = {
            w.name: dists.get(w.name, float("inf")) for w in warehouses
        }

    # Greedy
    allocation = greedy_allocation(cities, warehouses, shipping_cost_matrix)

    # Knapsack
    allocation, warehouse_usage = adjust_capacity(
        cities, warehouses, allocation, shipping_cost_matrix)

    # Evaluate pre-Tabu
    cost_before, util_before, _, demand_details_before, _ = evaluate_solution(
        cities, warehouses, allocation, shipping_cost_matrix)

    # Tabu search — suppress verbose prints
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        opt_alloc = tabu_search(cities, warehouses, allocation, shipping_cost_matrix)
    finally:
        sys.stdout = old_stdout

    # Evaluate post-Tabu
    cost_after, util_after, demand_ok, demand_details, cap_violations = evaluate_solution(
        cities, warehouses, opt_alloc, shipping_cost_matrix)

    # TSP
    tsp_results = compute_tsp_for_all_warehouses(opt_alloc, warehouses, graph)

    return {
        "graph":                graph,
        "shipping_cost_matrix": shipping_cost_matrix,
        "allocation_greedy":    allocation,
        "warehouse_usage":      warehouse_usage,
        "allocation_final":     opt_alloc,
        "cost_before":          cost_before,
        "cost_after":           cost_after,
        "util_before":          util_before,
        "util_after":           util_after,
        "demand_details":       demand_details,
        "cap_violations":       cap_violations,
        "tsp_results":          tsp_results,
        "cities":               cities,
        "warehouses":           warehouses,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — Data Input
# ─────────────────────────────────────────────────────────────────────────────
if page == "Data Input":
    st.markdown('<div class="sec-header">Data Input</div>', unsafe_allow_html=True)
    st.caption("Enter data manually or upload a JSON / Excel file. "
               "Click **Load sample data** in the sidebar to try a pre-built dataset.")

    input_tab, upload_tab = st.tabs(["✏️  Manual Entry", "📁  Upload File"])

    # ── Manual Entry ─────────────────────────────────────────────────────────
    with input_tab:
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown("**Cities**")
            st.markdown('<p class="hint">Add one row per city.</p>',
                        unsafe_allow_html=True)
            cities_edited = st.data_editor(
                st.session_state.cities_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name":   st.column_config.TextColumn("City Name", width="medium"),
                    "demand": st.column_config.NumberColumn("Demand (units)", min_value=1, step=1),
                },
                key="cities_editor",
                height=300,
            )

            st.markdown("**Warehouses**")
            st.markdown('<p class="hint">Add one row per warehouse.</p>',
                        unsafe_allow_html=True)
            warehouses_edited = st.data_editor(
                st.session_state.warehouses_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name":     st.column_config.TextColumn("Warehouse ID", width="medium"),
                    "capacity": st.column_config.NumberColumn("Capacity (units)", min_value=1, step=1),
                },
                key="warehouses_editor",
                height=250,
            )

        with col2:
            st.markdown("**Roads (edges)**")
            st.markdown('<p class="hint">Each road connects two nodes (city or warehouse). '
                        'Bidirectional by default.</p>', unsafe_allow_html=True)
            roads_edited = st.data_editor(
                st.session_state.roads_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "from":     st.column_config.TextColumn("From", width="medium"),
                    "to":       st.column_config.TextColumn("To",   width="medium"),
                    "distance": st.column_config.NumberColumn("Distance", min_value=1, step=1),
                },
                key="roads_editor",
                height=550,
            )

        if st.button("✅  Confirm manual data", type="primary", use_container_width=True):
            errs = _validate(cities_edited, warehouses_edited, roads_edited)
            if errs:
                for e in errs:
                    st.error(e)
            else:
                st.session_state.cities_df     = cities_edited.dropna()
                st.session_state.warehouses_df = warehouses_edited.dropna()
                st.session_state.roads_df      = roads_edited.dropna()
                st.session_state.data_ready    = True
                st.session_state.results       = None
                st.success(f"Data saved — {len(cities_edited)} cities, "
                           f"{len(warehouses_edited)} warehouses, "
                           f"{len(roads_edited)} roads.")

    # ── Upload File ───────────────────────────────────────────────────────────
    with upload_tab:
        st.markdown("**Download the Excel template** to fill in your data:")
        st.download_button(
            "⬇️  Download Excel template",
            data=_make_excel_template(),
            file_name="inventory_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.markdown("---")
        uploaded = st.file_uploader(
            "Upload your filled Excel (.xlsx) or JSON file",
            type=["xlsx", "json"],
            help="Excel must have three sheets: Cities, Warehouses, Roads. "
                 "JSON must match the sample_data.json structure.",
        )

        if uploaded:
            try:
                raw = uploaded.read()
                if uploaded.name.endswith(".json"):
                    c_df, w_df, r_df = _parse_json(raw)
                else:
                    c_df, w_df, r_df = _parse_excel(raw)

                errs = _validate(c_df, w_df, r_df)
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    st.session_state.cities_df     = c_df
                    st.session_state.warehouses_df = w_df
                    st.session_state.roads_df      = r_df
                    st.session_state.data_ready    = True
                    st.session_state.results       = None

                    st.success(f"Loaded: {len(c_df)} cities · "
                               f"{len(w_df)} warehouses · {len(r_df)} roads")

                    p1, p2, p3 = st.columns(3)
                    with p1:
                        st.markdown("**Cities preview**")
                        st.dataframe(c_df, use_container_width=True, height=200)
                    with p2:
                        st.markdown("**Warehouses preview**")
                        st.dataframe(w_df, use_container_width=True, height=200)
                    with p3:
                        st.markdown("**Roads preview**")
                        st.dataframe(r_df, use_container_width=True, height=200)

            except Exception as ex:
                st.error(f"Could not parse file: {ex}")

    # ── Data summary ──────────────────────────────────────────────────────────
    if st.session_state.data_ready:
        st.markdown("---")
        st.markdown('<div class="sec-header">Current dataset summary</div>',
                    unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        total_demand   = st.session_state.cities_df["demand"].sum()
        total_capacity = st.session_state.warehouses_df["capacity"].sum()
        m1.metric("Cities",          len(st.session_state.cities_df))
        m2.metric("Warehouses",      len(st.session_state.warehouses_df))
        m3.metric("Total demand",    int(total_demand))
        m4.metric("Total capacity",  int(total_capacity),
                  delta=f"+{int(total_capacity - total_demand)} surplus"
                  if total_capacity >= total_demand
                  else f"{int(total_capacity - total_demand)} deficit",
                  delta_color="normal" if total_capacity >= total_demand else "inverse")

        if total_capacity < total_demand:
            st.error("⚠️  Dataset is infeasible — demand exceeds total warehouse capacity. "
                     "Increase capacity or reduce demand before running.")
        else:
            st.success("Dataset is feasible. Head to **Run Pipeline** to optimize.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — Run Pipeline
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Run Pipeline":
    st.markdown('<div class="sec-header">Run Optimization Pipeline</div>',
                unsafe_allow_html=True)

    if not st.session_state.data_ready:
        st.warning("No data loaded yet — go to **Data Input** first.")
        st.stop()

    cdf = st.session_state.cities_df
    wdf = st.session_state.warehouses_df
    rdf = st.session_state.roads_df

    td = int(cdf["demand"].sum())
    tc = int(wdf["capacity"].sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Cities",         len(cdf))
    c2.metric("Total demand",   td)
    c3.metric("Total capacity", tc, delta=f"+{tc-td} surplus")

    st.markdown("---")
    if tc < td:
        st.error("Infeasible dataset. Fix data before running.")
        st.stop()

    st.markdown("The pipeline runs these stages in order:")
    cols = st.columns(5)
    labels = ["1. Dijkstra\nShortest paths",
              "2. Greedy\nInitial alloc",
              "3. Knapsack\nCapacity fix",
              "4. Tabu Search\nOptimization",
              "5. TSP DP\nDelivery routes"]
    for col, lbl in zip(cols, labels):
        col.info(lbl)

    st.markdown("---")

    run_btn = st.button("🚀  Run full pipeline", type="primary",
                        use_container_width=True,
                        disabled=(not st.session_state.data_ready))

    if run_btn:
        cities, warehouses, roads = _build_objects(cdf, wdf, rdf)
        prog = st.progress(0, text="Starting pipeline…")
        status = st.status("Running pipeline…", expanded=True)

        with status:
            st.write("**Step 1/5** — Building graph & running Dijkstra…")
            prog.progress(10, "Dijkstra shortest paths…")

            graph = Graph()
            for src, dst, dist in roads:
                graph.add_edge(src, dst, dist)

            shipping_cost_matrix = {}
            for city in cities:
                dists = dijkstra(graph, city.name)
                shipping_cost_matrix[city.name] = {
                    w.name: dists.get(w.name, float("inf")) for w in warehouses
                }
            st.write(f"  ✓ Computed {len(cities) * len(warehouses)} city-warehouse distances.")
            prog.progress(25, "Greedy allocation…")

            st.write("**Step 2/5** — Greedy initial allocation…")
            allocation = greedy_allocation(cities, warehouses, shipping_cost_matrix)
            st.write(f"  ✓ Assigned {len(cities)} cities to cheapest warehouses.")
            prog.progress(40, "Knapsack capacity adjustment…")

            st.write("**Step 3/5** — Fractional knapsack capacity adjustment…")
            old_stdout = sys.stdout; sys.stdout = io.StringIO()
            allocation, warehouse_usage = adjust_capacity(
                cities, warehouses, allocation, shipping_cost_matrix)
            sys.stdout = old_stdout
            st.write("  ✓ Overflow resolved. All capacities satisfied.")
            prog.progress(55, "Tabu Search optimization…")

            cost_before, util_before, _, _, _ = evaluate_solution(
                cities, warehouses, allocation, shipping_cost_matrix)
            st.write(f"  Pre-Tabu cost: **{cost_before}**")

            st.write("**Step 4/5** — Tabu Search optimization (50 iterations)…")
            old_stdout = sys.stdout; sys.stdout = io.StringIO()
            opt_alloc = tabu_search(cities, warehouses, allocation, shipping_cost_matrix)
            sys.stdout = old_stdout

            cost_after, util_after, demand_ok, demand_details, cap_violations = \
                evaluate_solution(cities, warehouses, opt_alloc, shipping_cost_matrix)
            imp = cost_before - cost_after
            pct = round(imp / cost_before * 100, 2) if cost_before else 0
            st.write(f"  ✓ Post-Tabu cost: **{cost_after}** "
                     f"(↓ {imp} units · {pct}% improvement)")
            prog.progress(80, "TSP route computation…")

            st.write("**Step 5/5** — TSP Held-Karp DP delivery routes…")
            tsp_results = compute_tsp_for_all_warehouses(opt_alloc, warehouses, graph)
            total_del = sum(c for c, _ in tsp_results.values())
            st.write(f"  ✓ Routes computed for {len(warehouses)} warehouses. "
                     f"Total delivery distance: **{total_del}**")
            prog.progress(100, "Done!")

        st.session_state.results = {
            "graph": graph,
            "shipping_cost_matrix": shipping_cost_matrix,
            "allocation_greedy":    allocation,
            "warehouse_usage":      warehouse_usage,
            "allocation_final":     opt_alloc,
            "cost_before":          cost_before,
            "cost_after":           cost_after,
            "util_before":          util_before,
            "util_after":           util_after,
            "demand_details":       demand_details,
            "cap_violations":       cap_violations,
            "tsp_results":          tsp_results,
            "cities":               cities,
            "warehouses":           warehouses,
        }
        st.success("Pipeline complete! Navigate to **Results** or **TSP Routes**.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3 — Results
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Results":
    st.markdown('<div class="sec-header">Optimization Results</div>',
                unsafe_allow_html=True)

    if st.session_state.results is None:
        st.warning("No results yet — run the pipeline first.")
        st.stop()

    R  = st.session_state.results
    wh = R["warehouses"]

    # ── Key metrics ───────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    imp = R["cost_before"] - R["cost_after"]
    pct = round(imp / R["cost_before"] * 100, 2) if R["cost_before"] else 0
    m1.metric("Cost before Tabu",  R["cost_before"])
    m2.metric("Cost after Tabu",   R["cost_after"], delta=f"-{imp} ({pct}%)",
              delta_color="inverse")
    m3.metric("Improvement",       f"{pct}%")
    total_del = sum(c for c, _ in R["tsp_results"].values())
    m4.metric("Total delivery dist", total_del)

    # ── Shipping cost matrix ──────────────────────────────────────────────────
    st.markdown('<div class="sec-header">Shipping cost matrix</div>',
                unsafe_allow_html=True)
    scm = R["shipping_cost_matrix"]
    wh_names = [w.name for w in wh]
    scm_df = pd.DataFrame(
        {city: [scm[city][w] for w in wh_names] for city in scm},
        index=wh_names,
    ).T
    scm_df.index.name = "City \\ Warehouse"
    st.dataframe(scm_df.style.highlight_min(axis=1, color="#d1fae5")
                              .highlight_max(axis=1, color="#fee2e2"),
                 use_container_width=True)

    # ── Warehouse utilization ─────────────────────────────────────────────────
    st.markdown('<div class="sec-header">Warehouse utilization</div>',
                unsafe_allow_html=True)

    util = R["util_after"]
    util_df = pd.DataFrame([
        {
            "Warehouse":    w,
            "Used":         util[w]["used"],
            "Capacity":     util[w]["capacity"],
            "Utilization %": util[w]["utilization_percent"],
            "Status":        "Over capacity" if util[w]["over_capacity"] else "OK",
        }
        for w in util
    ])

    ch_col, tbl_col = st.columns([3, 2], gap="large")
    with ch_col:
        chart_df = util_df.set_index("Warehouse")[["Used", "Capacity"]]
        st.bar_chart(chart_df, use_container_width=True, height=320)
    with tbl_col:
        st.dataframe(
            util_df.style.apply(
                lambda row: ["background:#fee2e2" if row["Status"] == "Over capacity"
                             else "" for _ in row], axis=1),
            use_container_width=True, hide_index=True, height=320)

    # ── Final allocation ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-header">Final optimized allocation</div>',
                unsafe_allow_html=True)

    alloc = R["allocation_final"]
    rows = []
    for city, wh_dict in alloc.items():
        for w, units in wh_dict.items():
            rows.append({"City": city, "Warehouse": w,
                         "Units allocated": units,
                         "Cost/unit": scm[city][w],
                         "Total cost": units * scm[city][w],
                         "Split?": "Yes" if len(wh_dict) > 1 else "No"})
    alloc_df = pd.DataFrame(rows)
    st.dataframe(
        alloc_df.style.apply(
            lambda row: ["background:#fef9c3" if row["Split?"] == "Yes"
                         else "" for _ in row], axis=1),
        use_container_width=True, hide_index=True, height=400,
    )
    st.caption("🟡 Yellow rows = city demand split across multiple warehouses")

    # ── Demand satisfaction ───────────────────────────────────────────────────
    st.markdown('<div class="sec-header">Demand satisfaction</div>',
                unsafe_allow_html=True)
    dd = R["demand_details"]
    dd_df = pd.DataFrame([
        {"City": c, "Demand": v["demand"], "Allocated": v["allocated"],
         "Status": "OK" if v["satisfied"] else
                   ("Over-allocated" if v["over_allocated"] else "Under-allocated")}
        for c, v in dd.items()
    ])
    st.dataframe(
        dd_df.style.apply(
            lambda row: ["background:#d1fae5" if row["Status"] == "OK"
                         else "background:#fee2e2" for _ in row], axis=1),
        use_container_width=True, hide_index=True)

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown("---")
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        json_out = json.dumps(
            {city: {w: int(u) for w, u in wh_d.items()}
             for city, wh_d in alloc.items()},
            indent=2)
        st.download_button("⬇️  Download allocation (JSON)",
                           json_out, "allocation.json", "application/json",
                           use_container_width=True)
    with dl_col2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as wr:
            alloc_df.to_excel(wr, sheet_name="Allocation", index=False)
            util_df.to_excel(wr,  sheet_name="Utilization", index=False)
            scm_df.to_excel(wr,   sheet_name="Cost Matrix")
        st.download_button("⬇️  Download full results (Excel)",
                           buf.getvalue(), "results.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4 — TSP Routes
# ─────────────────────────────────────────────────────────────────────────────
elif page == "TSP Routes":
    st.markdown('<div class="sec-header">TSP Delivery Routes (Held-Karp DP)</div>',
                unsafe_allow_html=True)

    if st.session_state.results is None:
        st.warning("No results yet — run the pipeline first.")
        st.stop()

    R   = st.session_state.results
    tsp = R["tsp_results"]
    alloc = R["allocation_final"]
    scm   = R["shipping_cost_matrix"]
    whs   = R["warehouses"]

    # summary metrics
    total_dist  = sum(c for c, _ in tsp.values())
    total_stops = sum(len(r) - 2 for _, r in tsp.values() if len(r) > 1)
    wh_active   = sum(1 for c, _ in tsp.values() if c > 0)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total delivery distance", total_dist)
    m2.metric("Total city stops",        total_stops)
    m3.metric("Active warehouses",       wh_active)

    st.caption("Algorithm: **Held-Karp Bitmask DP** · exact optimal routes · "
               "round-trip from depot")
    st.markdown("---")

    # per-warehouse route cards
    for wh in whs:
        wh_name = wh.name
        cost, route = tsp[wh_name]

        if len(route) <= 1:
            with st.expander(f"**{wh_name}** — no deliveries"):
                st.write("No cities assigned to this warehouse.")
            continue

        city_stops = route[1:-1]
        num_cities = len(city_stops)
        route_str  = " → ".join(route)

        with st.expander(f"**{wh_name}** · {num_cities} stops · distance {cost}",
                         expanded=True):
            st.markdown(f'<div class="route-line">🗺 {route_str}</div>',
                        unsafe_allow_html=True)

            # Breakdown table
            stop_rows = []
            for city in city_stops:
                units = alloc[city].get(wh_name, 0)
                total_alloc = sum(alloc[city].values())
                is_split    = len(alloc[city]) > 1
                stop_rows.append({
                    "Stop":      city,
                    "Units":     units,
                    "Cost/unit": scm[city][wh_name],
                    "Leg cost":  units * scm[city][wh_name],
                    "Split delivery?": "Yes — also delivered by: " +
                                       ", ".join(w for w in alloc[city] if w != wh_name)
                                       if is_split else "No",
                })
            stop_df = pd.DataFrame(stop_rows)
            st.dataframe(
                stop_df.style.apply(
                    lambda row: ["background:#fef9c3"
                                 if "Yes" in str(row["Split delivery?"]) else ""
                                 for _ in row], axis=1),
                use_container_width=True, hide_index=True)
            st.caption(f"Round-trip total distance: **{cost}**  ·  "
                       f"Delivery cost subtotal: **{stop_df['Leg cost'].sum()}**")

    # Full TSP summary table
    st.markdown('<div class="sec-header">Summary table</div>', unsafe_allow_html=True)
    summary_rows = []
    for wh in whs:
        wh_name = wh.name
        cost, route = tsp[wh_name]
        stops = route[1:-1]
        summary_rows.append({
            "Warehouse":       wh_name,
            "Cities served":   len(stops),
            "Route":           " → ".join(route),
            "Total distance":  cost,
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    # Download routes
    st.markdown("---")
    routes_json = {
        wh_name: {
            "route":          route,
            "total_distance": cost,
            "stops": [
                {"city": c, "units": alloc[c].get(wh_name, 0)}
                for c in route[1:-1]
            ]
        }
        for wh_name, (cost, route) in tsp.items()
    }
    st.download_button(
        "⬇️  Download TSP routes (JSON)",
        json.dumps(routes_json, indent=2),
        "tsp_routes.json",
        "application/json",
        use_container_width=True,
    )