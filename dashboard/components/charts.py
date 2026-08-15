import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

def create_risk_distribution_chart(low: int, medium: int, high: int):
    """Creates a Plotly Donut Chart for risk distribution with clean margins and label bounds."""
    total = low + medium + high
    if total == 0:
        fig = go.Figure(data=[go.Pie(
            labels=["No Data"],
            values=[1],
            hole=0.55,
            marker=dict(colors=["#374151"]),
            textinfo="none",
            hoverinfo="none"
        )])
        fig.update_layout(
            title_text="Employee Attrition Risk Tiers",
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E5E7EB"),
            margin=dict(t=60, b=30, l=30, r=30),
            annotations=[dict(text="No Predictions", x=0.5, y=0.5, font_size=14, showarrow=False, font_color="#9CA3AF")]
        )
        return fig

    # Filter out 0-count slices so 0% labels never overflow top margins
    labels_clean = []
    values_clean = []
    colors_clean = []

    if low > 0:
        labels_clean.append("Low Risk")
        values_clean.append(low)
        colors_clean.append("#10B981")
    if medium > 0:
        labels_clean.append("Medium Risk")
        values_clean.append(medium)
        colors_clean.append("#F59E0B")
    if high > 0:
        labels_clean.append("High Risk")
        values_clean.append(high)
        colors_clean.append("#EF4444")

    fig = go.Figure(data=[go.Pie(
        labels=labels_clean,
        values=values_clean,
        hole=0.55,
        marker=dict(colors=colors_clean),
        textinfo="label+percent",
        textposition="inside",
        hoverinfo="label+value+percent"
    )])

    fig.update_layout(
        title_text="Employee Attrition Risk Tiers",
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        margin=dict(t=70, b=40, l=40, r=40)
    )
    return fig

def create_department_risk_chart(dept_stats: List[Dict[str, Any]]):
    """Creates a Plotly Bar Chart showing average attrition risk per department/account."""
    if not dept_stats:
        return go.Figure()

    df = pd.DataFrame(dept_stats)
    df["avg_risk_pct"] = df["average_risk_probability"] * 100

    fig = px.bar(
        df,
        x="department",
        y="avg_risk_pct",
        color="avg_risk_pct",
        color_continuous_scale="Reds",
        labels={"department": "Department / Account", "avg_risk_pct": "Average Attrition Risk (%)"},
        title="Average Attrition Risk by Department / Account"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
        margin=dict(t=70, b=40, l=40, r=40)
    )
    return fig

def create_shap_impact_chart(factors: List[Dict[str, Any]]):
    """Creates a horizontal bar chart showing top SHAP factors driving risk."""
    if not factors:
        return go.Figure()

    df = pd.DataFrame(factors)
    df = df.sort_values(by="shap_value", ascending=True)

    df["color"] = df["shap_value"].apply(lambda v: "#EF4444" if v > 0 else "#10B981")

    fig = go.Figure(go.Bar(
        x=df["shap_value"],
        y=df["feature_name"],
        orientation="h",
        marker=dict(color=df["color"]),
        text=df["description"],
        hoverinfo="y+x+text"
    ))

    fig.update_layout(
        title="Top AI Risk Factors (SHAP Contributions)",
        xaxis_title="SHAP Value (Impact on Risk)",
        yaxis_title="Employee Attribute",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
        margin=dict(t=50, b=30, l=30, r=30)
    )
    return fig

def create_employee_risk_timeline_chart(timeline_records: List[Dict[str, Any]], employee_id: str):
    """Creates a Plotly Line Chart displaying an employee's historical risk trajectory over time (Before vs. Now)."""
    if not timeline_records:
        return go.Figure()

    df = pd.DataFrame(timeline_records)
    df["risk_pct"] = df["attrition_probability"] * 100

    fig = go.Figure()

    # Line plot of historical risk probability
    fig.add_trace(go.Scatter(
        x=df["created_at"],
        y=df["risk_pct"],
        mode="lines+markers",
        name="Attrition Risk %",
        line=dict(color="#3B82F6", width=3),
        marker=dict(size=10, color="#60A5FA", symbol="circle")
    ))

    # Add threshold reference lines for Risk Zones
    fig.add_hline(y=60, line_dash="dash", line_color="#EF4444", annotation_text="High Risk Threshold (60%)")
    fig.add_hline(y=30, line_dash="dash", line_color="#F59E0B", annotation_text="Medium Risk Threshold (30%)")

    fig.update_layout(
        title=f"📈 Historical Attrition Risk Trajectory for {employee_id} (Before vs. Now)",
        xaxis_title="Prediction Run Timestamp",
        yaxis_title="Attrition Risk Probability (%)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E5E7EB"),
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
        margin=dict(t=60, b=30, l=30, r=30)
    )
    return fig
