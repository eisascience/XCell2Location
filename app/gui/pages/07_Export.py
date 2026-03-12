"""Page 7: Export — export results to various formats."""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Export — XCell2Location", layout="wide")

st.title("📤 Export Results")
st.markdown("Export analysis results to CSV, Parquet, JSON, h5ad, and generate an R snippet.")

if st.session_state.get("results") is None:
    st.warning("⚠️ No results to export. Please complete **05 Run** first.")
    st.stop()

adata = st.session_state["results"]
output_dir = Path(st.session_state.get("output_dir", "output")) / "exports"

# ── Export options ─────────────────────────────────────────────────────────────

st.subheader("Export Options")

col1, col2 = st.columns(2)
with col1:
    export_csv = st.checkbox("CSV", value=True)
    export_parquet = st.checkbox("Parquet", value=True)
    export_json = st.checkbox("JSON", value=True)
with col2:
    export_h5ad = st.checkbox("h5ad", value=True)
    export_r = st.checkbox("R loading snippet", value=True)

abundance_key = st.text_input(
    "obsm key for cell abundance",
    value="q05_cell_abundance_w_sf",
    help="Key in adata.obsm containing cell abundance estimates.",
)

custom_dir = st.text_input("Export directory", value=str(output_dir))

if st.button("📤 Export", type="primary"):
    out = Path(custom_dir)
    out.mkdir(parents=True, exist_ok=True)

    formats = []
    if export_csv:
        formats.append("csv")
    if export_parquet:
        formats.append("parquet")
    if export_json:
        formats.append("json")

    exported = {}

    from app.io.exports import export_dataframe, export_h5ad as _export_h5ad, generate_r_snippet
    import pandas as pd

    # Export abundance
    if abundance_key in adata.obsm and formats:
        abund = adata.obsm[abundance_key]
        if not isinstance(abund, pd.DataFrame):
            abund = pd.DataFrame(abund, index=adata.obs_names)
        try:
            paths = export_dataframe(abund, out, "cell_abundance", formats)  # type: ignore[arg-type]
            exported.update(paths)
        except Exception as exc:
            st.error(f"Export failed: {exc}")

    # Save h5ad
    h5ad_path = None
    if export_h5ad:
        try:
            h5ad_path = _export_h5ad(adata, out, "results")
            exported["h5ad"] = h5ad_path
        except Exception as exc:
            st.error(f"h5ad export failed: {exc}")

    # R snippet
    if export_r:
        try:
            snippet = generate_r_snippet(
                h5ad_path,
                exported.get("csv"),
                out,
            )
            exported["R snippet"] = snippet
        except Exception as exc:
            st.error(f"R snippet generation failed: {exc}")

    if exported:
        st.success(f"✅ Export complete → `{out}`")
        st.subheader("Exported Files")
        for name, path in exported.items():
            col1, col2 = st.columns([1, 3])
            col1.write(f"**{name}**")
            col2.code(str(path))

            # Provide download button for small files
            try:
                if Path(path).stat().st_size < 50 * 1024 * 1024:  # 50 MB
                    with open(path, "rb") as f:
                        st.download_button(
                            f"⬇️ Download {name}",
                            data=f.read(),
                            file_name=Path(path).name,
                        )
            except Exception:
                pass
    else:
        st.warning("Nothing was exported. Select at least one format.")
