"""Page 4: Parameters — configure model parameters."""

import streamlit as st

st.set_page_config(page_title="Parameters — XCell2Location", layout="wide")

st.title("⚙️ Analysis Parameters")
st.markdown("Configure cell2location model and runtime parameters.")

# ── Device ────────────────────────────────────────────────────────────────────

st.subheader("Compute Device")

from app.core.device import device_info

info = device_info()
col1, col2, col3 = st.columns(3)
col1.metric("CUDA available", "Yes ✓" if info.get("cuda_available") else "No")
col2.metric("MPS available", "Yes ✓" if info.get("mps_available") else "No")
col3.metric("torch version", info.get("torch_version", "N/A"))

device = st.selectbox(
    "Compute Device",
    options=["auto", "cpu", "cuda", "mps"],
    help="'auto' selects the best available device (CUDA > MPS > CPU).",
)

# ── Cell2Location parameters ──────────────────────────────────────────────────

st.markdown("---")
st.subheader("Cell2Location Parameters")

col1, col2 = st.columns(2)
with col1:
    n_cells = st.number_input("N cells per location", value=30, min_value=1)
    detection_alpha = st.number_input("Detection alpha", value=20, min_value=1)
    max_epochs_ref = st.number_input("Max epochs (reference model)", value=250, min_value=1)

with col2:
    max_epochs_spatial = st.number_input("Max epochs (spatial model)", value=30000, min_value=1)
    batch_size = st.number_input("Batch size", value=2500, min_value=1)
    label_key = st.text_input("Label key (cell type column)", value="cell_type")

batch_key = st.text_input(
    "Batch key (optional, for reference model batch correction)", value=""
)

# ── Gene filter ───────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Gene Filtering")
col1, col2 = st.columns(2)
with col1:
    gene_filter_min_count = st.number_input("Min gene count (atlas filter)", value=10, min_value=0)
with col2:
    gene_filter_min_cells = st.number_input("Min cells expressing gene", value=3, min_value=0)

# ── Save parameters ───────────────────────────────────────────────────────────

st.markdown("---")
if st.button("💾 Save Parameters", type="primary"):
    params = {
        "device": device,
        "N_cells_per_location": int(n_cells),
        "detection_alpha": int(detection_alpha),
        "max_epochs_reference": int(max_epochs_ref),
        "max_epochs_spatial": int(max_epochs_spatial),
        "batch_size": int(batch_size),
        "label_key": label_key,
        "batch_key": batch_key or None,
        "gene_filter_min_count": int(gene_filter_min_count),
        "gene_filter_min_cells": int(gene_filter_min_cells),
    }
    st.session_state["run_params"] = params
    st.success("✓ Parameters saved.")

if st.session_state.get("run_params"):
    with st.expander("Current parameters"):
        import json
        st.code(json.dumps(st.session_state["run_params"], indent=2), language="json")
    st.markdown("➡️ Proceed to **05 Run**.")
