"""XCell2Location Streamlit application — main entry point."""

import streamlit as st

st.set_page_config(
    page_title="XCell2Location",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state initialisation ──────────────────────────────────────────────
if "config" not in st.session_state:
    st.session_state["config"] = None
if "adata_spatial" not in st.session_state:
    st.session_state["adata_spatial"] = None
if "adata_reference" not in st.session_state:
    st.session_state["adata_reference"] = None
if "results" not in st.session_state:
    st.session_state["results"] = None
if "output_dir" not in st.session_state:
    st.session_state["output_dir"] = "output"

# ── Landing page ──────────────────────────────────────────────────────────────

st.title("🔬 XCell2Location")
st.markdown(
    """
**Cross-platform spatial transcriptomics analysis platform**  
Powered by [cell2location](https://cell2location.readthedocs.io) · Seurat-friendly · Multi-platform

---

### Getting Started

Use the **sidebar** to navigate through the workflow:

| Step | Page | Description |
|------|------|-------------|
| 1 | 📁 Project Setup | Configure project name, output directory, and platform |
| 2 | 🗂 Atlas | Select or download a reference atlas (RIRA) |
| 3 | 🔍 QC | Run quality control and inspect metrics |
| 4 | ⚙️ Parameters | Configure model and analysis parameters |
| 5 | ▶️ Run | Execute the deconvolution pipeline |
| 6 | 📊 Results | Visualise and explore results |
| 7 | 📤 Export | Export results to CSV, Parquet, h5ad, R snippet |

---
"""
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Status", "Ready" if st.session_state["adata_spatial"] is None else "Data loaded")

with col2:
    if st.session_state["adata_spatial"] is not None:
        adata = st.session_state["adata_spatial"]
        st.metric("Spots / Cells", f"{adata.n_obs:,}")
    else:
        st.metric("Spots / Cells", "—")

with col3:
    if st.session_state["adata_spatial"] is not None:
        adata = st.session_state["adata_spatial"]
        st.metric("Genes", f"{adata.n_vars:,}")
    else:
        st.metric("Genes", "—")

st.info(
    "👈 Start by navigating to **01 Project Setup** in the sidebar.",
    icon="ℹ️",
)
