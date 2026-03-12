"""Page 2: Atlas — select, register, or download reference atlas."""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Atlas — XCell2Location", layout="wide")

st.title("🗂 Reference Atlas")
st.markdown("Select or register the single-cell reference atlas for deconvolution.")

# ── Current registry ──────────────────────────────────────────────────────────
try:
    from app.atlas.registry import get_default_registry

    registry = get_default_registry()
    entries = registry.list()
    atlas_ids = [e.atlas_id for e in entries]
except Exception as exc:
    st.error(f"Cannot load atlas registry: {exc}")
    st.stop()

st.subheader("Registered Atlases")
for entry in entries:
    cached = entry.local_path and Path(entry.local_path).exists()
    icon = "✅" if cached else "⬜"
    with st.expander(f"{icon} {entry.atlas_id} — {entry.name}"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Species:** {entry.species}")
            st.write(f"**Tissue:** {entry.tissue}")
            st.write(f"**Label key:** {entry.label_key}")
        with col2:
            st.write(f"**Version:** {entry.version}")
            st.write(f"**URL:** {entry.url or 'N/A'}")
            st.write(f"**Cached:** {'Yes ✓' if cached else 'No'}")
        st.write(f"**Description:** {entry.description}")

# ── Atlas selection ───────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Select Atlas")

col1, col2 = st.columns([2, 1])
with col1:
    selected_id = st.selectbox("Atlas ID", options=atlas_ids + ["custom"])

with col2:
    if st.button("Use Selected Atlas"):
        if selected_id != "custom":
            try:
                entry = registry.get(selected_id)
                if entry.local_path and Path(entry.local_path).exists():
                    import anndata as ad

                    ref = ad.read_h5ad(entry.local_path)
                    st.session_state["adata_reference"] = ref
                    st.session_state["atlas_id"] = selected_id
                    st.success(f"✓ Loaded atlas: {ref.n_obs:,} cells × {ref.n_vars:,} genes")
                else:
                    st.warning(f"Atlas '{selected_id}' is not cached locally. Download it below.")
            except Exception as exc:
                st.error(f"Error: {exc}")

# ── Download ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Download Atlas")

download_id = st.selectbox("Atlas to download", options=atlas_ids, key="download_id_select")
if st.button("Download"):
    try:
        entry = registry.get(download_id)
        if entry.url is None:
            st.error("No URL configured for this atlas.")
        else:
            cache_dir = Path("~/.xcell2location/atlas_cache").expanduser()
            dest = cache_dir / f"{download_id}.h5ad"

            from app.atlas.downloader import download_atlas

            with st.spinner(f"Downloading {download_id}…"):
                path = download_atlas(entry.url, dest, expected_sha256=entry.sha256)
                registry.update_local_path(download_id, path)
            st.success(f"✓ Downloaded to {path}")
    except Exception as exc:
        st.error(f"Download failed: {exc}")

# ── Register local file ───────────────────────────────────────────────────────

st.markdown("---")
with st.expander("Register Local Atlas"):
    new_id = st.text_input("Atlas ID", key="new_atlas_id")
    new_name = st.text_input("Name", key="new_atlas_name")
    new_path = st.text_input("Local h5ad path", key="new_atlas_path")
    new_species = st.text_input("Species", value="human", key="new_atlas_species")
    new_tissue = st.text_input("Tissue", value="pan-tissue", key="new_atlas_tissue")
    new_label = st.text_input("Label key", value="cell_type", key="new_atlas_label")

    if st.button("Register"):
        if not (new_id and new_name and new_path):
            st.error("Please fill in all required fields.")
        elif not Path(new_path).exists():
            st.error(f"File not found: {new_path}")
        else:
            from app.atlas.registry import AtlasEntry

            entry = AtlasEntry(
                atlas_id=new_id,
                name=new_name,
                description=f"User-registered: {new_name}",
                url=None,
                sha256=None,
                local_path=new_path,
                species=new_species,
                tissue=new_tissue,
                label_key=new_label,
            )
            try:
                registry.register(entry)
                st.success(f"✓ Registered atlas: {new_id}")
                st.rerun()
            except Exception as exc:
                st.error(f"Registration failed: {exc}")

# ── Status ────────────────────────────────────────────────────────────────────

if st.session_state.get("adata_reference") is not None:
    ref = st.session_state["adata_reference"]
    st.markdown("---")
    st.success(f"✓ Reference loaded: {ref.n_obs:,} cells × {ref.n_vars:,} genes")
    st.markdown("➡️ Proceed to **03 QC**.")
