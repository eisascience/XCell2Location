"""Page 5: Run — execute the analysis pipeline."""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Run — XCell2Location", layout="wide")

st.title("▶️ Run Analysis")
st.markdown("Execute the cell2location spatial deconvolution pipeline.")

# ── Pre-flight checks ─────────────────────────────────────────────────────────

issues = []
if st.session_state.get("adata_spatial") is None:
    issues.append("No spatial data loaded (go to 01 Project Setup)")
if st.session_state.get("run_params") is None:
    issues.append("Parameters not configured (go to 04 Parameters)")

if issues:
    st.warning("⚠️ Please complete these steps first:")
    for issue in issues:
        st.markdown(f"  - {issue}")
    st.stop()

adata_spatial = st.session_state["adata_spatial"]
adata_reference = st.session_state.get("adata_reference")
params = st.session_state["run_params"]
output_dir = Path(st.session_state.get("output_dir", "output"))
platform = st.session_state.get("platform", "visium")

# ── Summary ───────────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)
col1.metric("Spatial spots", f"{adata_spatial.n_obs:,}")
col2.metric("Reference cells", f"{adata_reference.n_obs:,}" if adata_reference else "—")
col3.metric("Platform", platform)

st.markdown("---")

with st.expander("Run configuration"):
    import json
    st.code(json.dumps(params, indent=2), language="json")

# ── Execute ───────────────────────────────────────────────────────────────────

if st.button("🚀 Run cell2location", type="primary"):
    progress = st.progress(0, text="Initialising…")
    log_box = st.empty()

    try:
        progress.progress(10, text="Setting up backend…")

        if platform == "visiumhd":
            from app.models.visiumhd_backend import VisiumHDBackend
            backend = VisiumHDBackend(params, output_dir)
        elif platform == "cosmx":
            from app.models.cosmx_backend import CosMxBackend
            backend = CosMxBackend(params, output_dir)
        elif platform == "phenocycler":
            from app.models.phenocycler_backend import PhenoCyclerBackend
            backend = PhenoCyclerBackend(params, output_dir)
        else:
            from app.models.visium_backend import VisiumBackend
            backend = VisiumBackend(params, output_dir)

        backend.setup(adata_spatial, adata_reference)
        progress.progress(30, text="Backend configured. Training model…")

        result = backend.run()
        progress.progress(80, text="Exporting results…")

        paths = backend.export_results(output_dir)
        st.session_state["results"] = result
        st.session_state["results_paths"] = paths

        progress.progress(100, text="Done!")
        st.success("✅ Analysis complete!")

        for key, path in paths.items():
            st.markdown(f"- **{key}**: `{path}`")

    except Exception as exc:
        progress.empty()
        st.error(f"❌ Run failed: {exc}")
        st.exception(exc)

if st.session_state.get("results") is not None:
    st.markdown("---")
    st.success("Results are available. ➡️ Proceed to **06 Results**.")
