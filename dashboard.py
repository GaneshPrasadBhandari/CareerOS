"""Executive analytics dashboard components for CareerOS."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import select

from database import EmailLog, JobApplication, get_session


STATUS_ORDER = ["Draft", "Approved", "Applied", "Follow-up", "Interview", "Job Offer"]


def _load_applications_df() -> pd.DataFrame:
    with get_session() as session:
        rows = session.scalars(select(JobApplication)).all()
    return pd.DataFrame(
        [
            {
                "Application_ID": r.application_id,
                "Company": r.company,
                "Role": r.role,
                "Status": r.status,
                "Match_Score": r.match_score,
                "Created": r.created_at,
            }
            for r in rows
        ]
    )


def _load_email_logs_df() -> pd.DataFrame:
    with get_session() as session:
        rows = session.scalars(select(EmailLog)).all()
    return pd.DataFrame(
        [
            {
                "Application_ID": r.application_id,
                "Provider": r.provider,
                "Recipient": r.recipient,
                "Status": r.status,
                "Created": r.created_at,
            }
            for r in rows
        ]
    )


def render_dashboard() -> None:
    st.subheader("📊 CareerOS Executive Dashboard")

    apps_df = _load_applications_df()
    if apps_df.empty:
        st.info("No applications stored yet.")
    else:
        apps_df["Status"] = pd.Categorical(apps_df["Status"], categories=STATUS_ORDER, ordered=True)
        funnel = apps_df.groupby("Status", observed=False).size().reset_index(name="Count")
        funnel = funnel.sort_values("Status")
        fig_funnel = px.funnel(funnel, x="Count", y="Status", title="Application Funnel (Matches to Offers)")
        st.plotly_chart(fig_funnel, use_container_width=True)

        applied = apps_df[apps_df["Status"].isin(["Applied", "Follow-up", "Interview", "Job Offer"])].copy()
        if not applied.empty:
            applied["Follow-up 3d"] = applied["Created"] + timedelta(days=3)
            applied["Follow-up 7d"] = applied["Created"] + timedelta(days=7)
            timeline = pd.melt(
                applied,
                id_vars=["Application_ID", "Company"],
                value_vars=["Follow-up 3d", "Follow-up 7d"],
                var_name="Reminder",
                value_name="Date",
            )
            fig_timeline = px.scatter(
                timeline,
                x="Date",
                y="Company",
                color="Reminder",
                title="Follow-up Timeline",
                hover_data=["Application_ID"],
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

    st.markdown("#### Sent Email Logs")
    logs_df = _load_email_logs_df()
    if logs_df.empty:
        st.caption("No email events yet.")
    else:
        st.dataframe(logs_df.sort_values("Created", ascending=False), use_container_width=True)
        st.caption(f"Last refresh: {datetime.utcnow().isoformat()}Z")
