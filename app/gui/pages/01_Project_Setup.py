"""Page 1: Project Setup — configure project and load spatial data."""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Project Setup — XCell2Location", layout="wide")

st.title("📁 Project Setup")
st.markdown("Configure your project and load the spatial data file.")

# ── Project settings ──────────────────────────────────────────────────────────

with st.expander("Project Settings", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input(
            "Project Name",
            value=st.session_state.get("project_name", "My XCell2Location Project"),
        )
    with col2:
        output_dir = st.text_input(
            "Output Directory",
            value=st.session_state.get("output_dir", "output"),
        )

    platform = st.selectbox(
        "Spatial Platform",
        options=["visium", "visiumhd", "cosmx", "phenocycler"],
        index=0,
        help="The spatial transcriptomics platform used to generate the data.",
    )

    random_seed = st.number_input("Random Seed", value=42, min_value=0)

    if st.button("Save Project Settings"):
        st.session_state["project_name"] = project_name
        st.session_state["output_dir"] = output_dir
        st.session_state["platform"] = platform
        st.session_state["random_seed"] = int(random_seed)

        # Create output directory
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        st.success(f"✓ Project settings saved. Output: {out.resolve()}")

# ── Data loading ──────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Load Spatial Data")

load_mode = st.radio(
    "Input Source",
    options=["Upload file", "Enter file path"],
    horizontal=True,
)

if load_mode == "Upload file":
    uploaded = st.file_uploader(
        "Upload h5ad file",
        type=["h5ad"],
        help="Upload your spatial transcriptomics data as h5ad.",
    )
    if uploaded is not None:
        import tempfile
        import anndata as ad

        with tempfile.NamedTemporaryFile(suffix=".h5ad", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        try:
            adata = ad.read_h5ad(tmp_path)
            st.session_state["adata_spatial"] = adata
            st.success(f"✓ Loaded: {adata.n_obs:,} spots × {adata.n_vars:,} genes")
        except Exception as exc:
            st.error(f"Failed to load: {exc}")

else:
    file_path = st.text_input("File Path", placeholder="/path/to/spatial_data.h5ad")
    if st.button("Load File") and file_path:
        p = Path(file_path)
        if not p.exists():
            st.error(f"File not found: {p}")
        else:
            import anndata as ad

            try:
                adata = ad.read_h5ad(p)
                st.session_state["adata_spatial"] = adata
                st.success(f"✓ Loaded: {adata.n_obs:,} spots × {adata.n_vars:,} genes")
            except Exception as exc:
                st.error(f"Failed to load: {exc}")

# ── Current data summary ──────────────────────────────────────────────────────

if st.session_state.get("adata_spatial") is not None:
    adata = st.session_state["adata_spatial"]
    st.markdown("---")
    st.subheader("Loaded Data Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Spots / Cells", f"{adata.n_obs:,}")
    col2.metric("Genes", f"{adata.n_vars:,}")
    col3.metric("Has Spatial Coords", "Yes" if "spatial" in adata.obsm else "No")
    col4.metric("Obs Columns", str(len(adata.obs.columns)))

    with st.expander("obs (metadata) preview"):
        st.dataframe(adata.obs.head(10))

    st.markdown("➡️ Proceed to **02 Atlas** to configure the reference atlas.")
