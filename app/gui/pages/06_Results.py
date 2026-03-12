"""Page 6: Results — visualise and explore deconvolution results."""

import streamlit as st

st.set_page_config(page_title="Results — XCell2Location", layout="wide")

st.title("📊 Results")
st.markdown("Explore spatial cell-type abundance and co-localisation.")

if st.session_state.get("results") is None:
    st.warning("⚠️ No results available. Please complete **05 Run** first.")
    st.stop()

import pandas as pd
import numpy as np
import plotly.express as px

adata = st.session_state["results"]

# ── Cell abundance ────────────────────────────────────────────────────────────

abundance_key = "q05_cell_abundance_w_sf"
has_abundance = abundance_key in adata.obsm

tab1, tab2, tab3, tab4 = st.tabs(["Cell Abundance", "Spatial Map", "Co-localisation", "Raw Data"])

with tab1:
    if has_abundance:
        abund = adata.obsm[abundance_key]
        if not isinstance(abund, pd.DataFrame):
            abund = pd.DataFrame(abund, index=adata.obs_names)

        st.subheader("Cell Type Abundances")
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_ct = st.multiselect(
                "Select cell types",
                options=list(abund.columns),
                default=list(abund.columns[:5]) if len(abund.columns) >= 5 else list(abund.columns),
            )
        with col2:
            chart_type = st.radio("Chart type", ["bar", "violin", "box"])

        if selected_ct:
            plot_df = abund[selected_ct].melt(var_name="Cell Type", value_name="Abundance")
            if chart_type == "bar":
                fig = px.bar(
                    abund[selected_ct].mean().reset_index(),
                    x="index",
                    y=0,
                    labels={"index": "Cell Type", 0: "Mean Abundance"},
                    title="Mean Cell Type Abundance per Spot",
                )
            elif chart_type == "violin":
                fig = px.violin(plot_df, x="Cell Type", y="Abundance", box=True)
            else:
                fig = px.box(plot_df, x="Cell Type", y="Abundance")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No cell abundance data found in obsm.")

with tab2:
    if "spatial" in adata.obsm and has_abundance:
        abund = adata.obsm[abundance_key]
        if not isinstance(abund, pd.DataFrame):
            abund = pd.DataFrame(abund, index=adata.obs_names)

        coords = adata.obsm["spatial"]
        plot_ct = st.selectbox("Cell type to plot", options=list(abund.columns))
        if plot_ct:
            df_plot = pd.DataFrame({
                "x": coords[:, 0],
                "y": coords[:, 1],
                "abundance": abund[plot_ct].values,
            })
            fig = px.scatter(
                df_plot,
                x="x",
                y="y",
                color="abundance",
                color_continuous_scale="viridis",
                title=f"Spatial distribution: {plot_ct}",
                size_max=6,
            )
            fig.update_traces(marker=dict(size=4))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Spatial coordinates or abundance data not available.")

with tab3:
    if has_abundance:
        from app.analysis.coloc import compute_colocalisation_matrix

        abund = adata.obsm[abundance_key]
        if not isinstance(abund, pd.DataFrame):
            abund = pd.DataFrame(abund, index=adata.obs_names)

        try:
            corr = abund.corr()
            fig = px.imshow(
                corr,
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title="Cell Type Co-localisation (Pearson r)",
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Co-localisation plot failed: {exc}")
    else:
        st.info("No abundance data available.")

with tab4:
    st.write(f"**Shape:** {adata.n_obs} × {adata.n_vars}")
    st.write("**obs columns:**", list(adata.obs.columns))
    st.write("**obsm keys:**", list(adata.obsm.keys()))
    st.write("**uns keys:**", list(adata.uns.keys()))
    with st.expander("obs preview"):
        st.dataframe(adata.obs.head(10))

st.markdown("➡️ Proceed to **07 Export**.")
