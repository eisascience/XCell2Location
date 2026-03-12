"""Page 3: QC — run quality control and inspect metrics."""

import streamlit as st

st.set_page_config(page_title="QC — XCell2Location", layout="wide")

st.title("🔍 Quality Control")
st.markdown("Run QC filtering and inspect per-cell metrics.")

if st.session_state.get("adata_spatial") is None:
    st.warning("⚠️ No spatial data loaded. Please complete **01 Project Setup** first.")
    st.stop()

adata = st.session_state["adata_spatial"]
platform = st.session_state.get("platform", "visium")

# ── QC parameters ─────────────────────────────────────────────────────────────

with st.expander("QC Parameters", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        mt_prefix = st.text_input("Mitochondrial gene prefix", value="MT-")
        min_genes = st.number_input("Min genes per cell", value=200, min_value=0)
        max_genes = st.number_input("Max genes per cell", value=6000, min_value=1)
    with col2:
        min_counts = st.number_input("Min total counts", value=500, min_value=0)
        max_pct_mt = st.slider("Max mitochondrial %", 0.0, 100.0, 20.0, step=0.5)
        batch_key = st.text_input("Batch key (optional)", value="")

    run_qc_btn = st.button("▶ Run QC", type="primary")

if run_qc_btn:
    from app.analysis.qc import run_qc
    from pathlib import Path

    output_dir = Path(st.session_state.get("output_dir", "output"))

    with st.spinner("Running QC…"):
        try:
            adata_qc = run_qc(
                adata,
                platform=platform,
                mt_prefix=mt_prefix,
                batch_key=batch_key or None,
                generate_plots=False,
                output_dir=output_dir,
            )
            st.session_state["adata_spatial"] = adata_qc
            st.success(f"✓ QC complete: {adata_qc.n_obs:,} spots retained (from {adata.n_obs:,})")
        except Exception as exc:
            st.error(f"QC failed: {exc}")

# ── Metrics display ───────────────────────────────────────────────────────────

adata_current = st.session_state["adata_spatial"]

if "total_counts" in adata_current.obs.columns:
    st.markdown("---")
    st.subheader("QC Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Median total counts", f"{adata_current.obs['total_counts'].median():.0f}")

    if "n_genes_by_counts" in adata_current.obs.columns:
        col2.metric("Median genes", f"{adata_current.obs['n_genes_by_counts'].median():.0f}")

    if "pct_counts_mt" in adata_current.obs.columns:
        col3.metric("Median MT%", f"{adata_current.obs['pct_counts_mt'].median():.1f}%")

    # Distribution plots
    import pandas as pd
    import plotly.express as px

    obs_df = adata_current.obs.copy()
    qc_cols = [c for c in ["total_counts", "n_genes_by_counts", "pct_counts_mt"] if c in obs_df.columns]

    if qc_cols:
        tab_labels = qc_cols
        tabs = st.tabs(tab_labels)
        for tab, col in zip(tabs, qc_cols):
            with tab:
                fig = px.histogram(obs_df, x=col, nbins=50, title=col)
                st.plotly_chart(fig, use_container_width=True)

st.markdown("➡️ Proceed to **04 Parameters**.")
