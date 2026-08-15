import sys
from pathlib import Path

# Add project root directory to sys.path for Streamlit execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import io
import json
import os
import datetime
import pandas as pd
import requests
import streamlit as st

# Configure Page Config
st.set_page_config(
    page_title="Enterprise Attrition System",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom Enterprise CSS Styling
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
    }
    .stApp {
        background: radial-gradient(circle at top left, #1A1F2C, #0E1117);
    }
    .css-1d38157 {
        background-color: #161B26;
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 15px;
    }
    .rec-card-high {
        border-left: 4px solid #EF4444;
        background-color: rgba(239, 68, 68, 0.08);
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .rec-card-medium {
        border-left: 4px solid #F59E0B;
        background-color: rgba(245, 158, 11, 0.08);
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .rec-card-low {
        border-left: 4px solid #10B981;
        background-color: rgba(16, 185, 129, 0.08);
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    /* Mandatory Red Asterisk Label Styling */
    .req-star {
        color: #EF4444 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        margin-left: 2px !important;
    }
    /* Green Submit Button Styling */
    div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #10B981, #059669) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    div.stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #059669, #047857) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6) !important;
        transform: translateY(-1px) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Helper for Dynamic Table Height
def get_table_height(data, min_h=95, max_h=450, row_h=38, header_h=40):
    if data is None:
        return min_h
    count = len(data)
    if count == 0:
        return min_h
    calc = header_h + (count * row_h)
    return min(max(calc, min_h), max_h)

# Module reloads to prevent Python bytecode caching issues
import importlib
import src.database.repository
import src.services.dashboard_service
import src.services.prediction_service
import src.ml.recommender

importlib.reload(src.database.repository)
importlib.reload(src.services.dashboard_service)
importlib.reload(src.services.prediction_service)
importlib.reload(src.ml.recommender)

from dashboard.components.kpi_cards import render_kpi_card, render_risk_badge
from dashboard.components.charts import (
    create_risk_distribution_chart,
    create_department_risk_chart,
    create_shap_impact_chart,
    create_employee_risk_timeline_chart
)
from src.config.settings import settings
from src.database.connection import SessionLocal, init_db
from src.services.prediction_service import PredictionService
from src.services.dashboard_service import DashboardService

# Navigation State Management
NAV_OPTIONS = [
    "📊 Executive Overview",
    "👤 Individual Predictor",
    "📁 Batch Predictor",
    "📜 Prediction Audit Logs"
]

if "menu_selection" not in st.session_state:
    st.session_state["menu_selection"] = NAV_OPTIONS[0]

# Header Banner
st.title("💼 Enterprise Employee Attrition Prediction System")
st.caption("AI-Powered Attrition Risk Forecasting, Explainable AI (SHAP), & HR Retention Recommendations")

# Sidebar Navigation Setup
st.sidebar.image("https://img.icons8.com/color/96/000000/analytics.png", width=70)
st.sidebar.title("Navigation Menu")

current_index = NAV_OPTIONS.index(st.session_state["menu_selection"]) if st.session_state["menu_selection"] in NAV_OPTIONS else 0
menu = st.sidebar.radio(
    "Select Module",
    NAV_OPTIONS,
    index=current_index,
    key="sidebar_radio"
)
st.session_state["menu_selection"] = menu

# Helper for Executive Filter Reset
def reset_executive_filters():
    st.session_state["filter_dept"] = "All"
    st.session_state["filter_role"] = "All"
    st.session_state["filter_risk"] = "All"
    st.session_state["filter_emp"] = "All"
    st.session_state["filter_ot"] = "All"
    st.session_state["filter_dates"] = []

# Helper for Individual Predictor Form Reset
def reset_individual_form():
    st.session_state["indiv_emp_id"] = "EMP-9999"
    st.session_state["indiv_full_name"] = "Alexander Wright"
    st.session_state["indiv_age"] = 34
    st.session_state["indiv_gender"] = "Male"
    st.session_state["indiv_department"] = "Research & Development"
    st.session_state["indiv_job_role"] = "Research Scientist"
    st.session_state["indiv_education_field"] = "Life Sciences"
    st.session_state["indiv_monthly_income"] = 3800.0
    st.session_state["indiv_overtime"] = "Yes"
    st.session_state["indiv_total_working_years"] = 8
    st.session_state["indiv_years_at_company"] = 3
    st.session_state["indiv_years_in_current_role"] = 2
    st.session_state["indiv_years_since_last_promotion"] = 3
    st.session_state["indiv_years_with_curr_manager"] = 1
    st.session_state["indiv_num_companies_worked"] = 4
    st.session_state["indiv_job_sat"] = 1
    st.session_state["individual_prediction_result"] = None

# ==============================================================================
# MODULE 1: EXECUTIVE OVERVIEW
# ==============================================================================
if menu == "📊 Executive Overview":
    st.header("Executive HR Analytics Overview")

    db = SessionLocal()
    try:
        dash_service = DashboardService(db)
        all_emp_records = dash_service.get_employees(limit=1000)

        # Initialize Session State Filter Keys
        if "filter_dept" not in st.session_state:
            st.session_state["filter_dept"] = "All"
        if "filter_role" not in st.session_state:
            st.session_state["filter_role"] = "All"
        if "filter_risk" not in st.session_state:
            st.session_state["filter_risk"] = "All"
        if "filter_emp" not in st.session_state:
            st.session_state["filter_emp"] = "All"
        if "filter_ot" not in st.session_state:
            st.session_state["filter_ot"] = "All"
        if "filter_dates" not in st.session_state:
            st.session_state["filter_dates"] = []

        # Interactive Global Filter Controls Header
        f_header_col1, f_header_col2 = st.columns([3, 1])
        with f_header_col1:
            st.subheader("🔍 Dynamic Analytics Filters")
        with f_header_col2:
            st.button("🔄 Reset All Filters", on_click=reset_executive_filters)

        f_row1_col1, f_row1_col2, f_row1_col3 = st.columns(3)
        f_row2_col1, f_row2_col2, f_row2_col3 = st.columns(3)

        # 1. Department List
        all_depts = ["All"] + sorted(list(set(e["department"] for e in all_emp_records if e.get("department"))))
        selected_dept = f_row1_col1.selectbox("Department / Account Filter", all_depts, key="filter_dept")

        # 2. Dynamic Job Role List based on Department
        if selected_dept != "All":
            filtered_by_dept = [e for e in all_emp_records if e.get("department") == selected_dept]
        else:
            filtered_by_dept = all_emp_records
        all_roles = ["All"] + sorted(list(set(e["job_role"] for e in filtered_by_dept if e.get("job_role"))))

        selected_role = f_row1_col2.selectbox("Job Role Filter", all_roles, key="filter_role")
        selected_risk = f_row1_col3.selectbox("Risk Level Tier Filter", ["All", "High", "Medium", "Low"], key="filter_risk")

        # 3. Dynamic Employee ID List based on selected Dept & Role
        filtered_by_role = filtered_by_dept
        if selected_role != "All":
            filtered_by_role = [e for e in filtered_by_dept if e.get("job_role") == selected_role]
        all_emp_ids = ["All"] + sorted(list(set(e["employee_id"] for e in filtered_by_role if e.get("employee_id"))))

        selected_emp_filter = f_row2_col1.selectbox("Employee ID Filter", all_emp_ids, key="filter_emp")
        selected_ot_filter = f_row2_col2.selectbox("Overtime Status Filter", ["All", "Yes", "No"], key="filter_ot")

        # 4. Single Date Range Filter (Leave blank for All Time)
        date_selection = f_row2_col3.date_input("Analysis Date Range Filter", value=[], key="filter_dates", help="Select start and end dates, or leave empty for All Time (Full Range)")
        
        start_date = None
        end_date = None
        if isinstance(date_selection, (list, tuple)):
            if len(date_selection) > 0:
                start_date = date_selection[0]
            if len(date_selection) > 1:
                end_date = date_selection[1]

        # Fetch metrics based on active multi-dimensional filters
        metrics = dash_service.get_dashboard_metrics(
            department_filter=selected_dept,
            job_role_filter=selected_role,
            risk_level_filter=selected_risk,
            employee_id_filter=selected_emp_filter,
            overtime_filter=selected_ot_filter,
            start_date=start_date,
            end_date=end_date
        )

        st.markdown("---")

        if metrics.get("total_employees", 0) == 0:
            st.info(f"ℹ️ No active employees found matching the filter criteria. Try clicking 'Reset All Filters'.")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            render_kpi_card("Total Employees", f"{metrics['total_employees']:,}", "Active Workforce Pool", "#3B82F6", "👥")
        with col2:
            pred_count = metrics.get("predicted_employees_count", metrics["total_employees"])
            missing_count = metrics.get("missing_predictions_count", 0)
            subtext = f"⚠️ {missing_count:,} Missing Predictions" if missing_count > 0 else "100% Workforce Evaluated"
            card_color = "#F59E0B" if missing_count > 0 else "#06B6D4"
            render_kpi_card("Predicted Employees", f"{pred_count:,}", subtext, card_color, "🎯")
        with col3:
            render_kpi_card("Avg Attrition Risk", f"{metrics['overall_attrition_rate']*100:.1f}%", "Baseline Filtered Average", "#8B5CF6", "📈")
        with col4:
            render_kpi_card("High Risk Employees", f"{metrics['high_risk_count']:,}", "Immediate HR Intervention Required", "#EF4444", "⚠️")
        with col5:
            render_kpi_card("Total Predictions", f"{metrics['total_predictions']:,}", "Logged Prediction Audits", "#10B981", "🛡️")

        st.markdown("---")

        c1, c2 = st.columns([1, 1])
        with c1:
            donut_fig = create_risk_distribution_chart(
                metrics["low_risk_count"],
                metrics["medium_risk_count"],
                metrics["high_risk_count"]
            )
            st.plotly_chart(donut_fig, use_container_width=True)

        with c2:
            dept_fig = create_department_risk_chart(metrics["department_statistics"])
            st.plotly_chart(dept_fig, use_container_width=True)

        st.markdown("---")

        # 5. Filtered Employee Roster Table Below Charts (Dynamic Height, Hidden Index Column)
        st.subheader("📋 Filtered Employee Workforce Details")
        roster_records = dash_service.get_filtered_employee_roster(
            department_filter=selected_dept,
            job_role_filter=selected_role,
            risk_level_filter=selected_risk,
            employee_id_filter=selected_emp_filter,
            overtime_filter=selected_ot_filter,
            limit=500
        )

        if roster_records:
            st.dataframe(
                pd.DataFrame(roster_records),
                height=get_table_height(roster_records),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No employee records match the active filter selection.")

    finally:
        db.close()

# ==============================================================================
# MODULE 2: INDIVIDUAL PREDICTOR (AUTOFILL FROM EXISTING EMPLOYEE ID)
# ==============================================================================
elif menu == "👤 Individual Predictor":
    db = SessionLocal()
    try:
        dash_service = DashboardService(db)
        registered_employees = dash_service.get_employees(limit=1000)
        registered_emp_ids = sorted(list(set(e["employee_id"] for e in registered_employees if e.get("employee_id"))))
    finally:
        db.close()

    # Initialize Form State Keys
    if "indiv_emp_id" not in st.session_state:
        st.session_state["indiv_emp_id"] = "EMP-9999"
    if "indiv_full_name" not in st.session_state:
        st.session_state["indiv_full_name"] = "Alexander Wright"
    if "indiv_age" not in st.session_state:
        st.session_state["indiv_age"] = 34
    if "indiv_gender" not in st.session_state:
        st.session_state["indiv_gender"] = "Male"
    if "indiv_department" not in st.session_state:
        st.session_state["indiv_department"] = "Research & Development"
    if "indiv_job_role" not in st.session_state:
        st.session_state["indiv_job_role"] = "Research Scientist"
    if "indiv_education_field" not in st.session_state:
        st.session_state["indiv_education_field"] = "Life Sciences"
    if "indiv_monthly_income" not in st.session_state:
        st.session_state["indiv_monthly_income"] = 3800.0
    if "indiv_overtime" not in st.session_state:
        st.session_state["indiv_overtime"] = "Yes"
    if "indiv_total_working_years" not in st.session_state:
        st.session_state["indiv_total_working_years"] = 8
    if "indiv_years_at_company" not in st.session_state:
        st.session_state["indiv_years_at_company"] = 3
    if "indiv_years_in_current_role" not in st.session_state:
        st.session_state["indiv_years_in_current_role"] = 2
    if "indiv_years_since_last_promotion" not in st.session_state:
        st.session_state["indiv_years_since_last_promotion"] = 3
    if "indiv_years_with_curr_manager" not in st.session_state:
        st.session_state["indiv_years_with_curr_manager"] = 1
    if "indiv_num_companies_worked" not in st.session_state:
        st.session_state["indiv_num_companies_worked"] = 4
    if "indiv_job_sat" not in st.session_state:
        st.session_state["indiv_job_sat"] = 1
    if "individual_prediction_result" not in st.session_state:
        st.session_state["individual_prediction_result"] = None

    p_header_col1, p_header_col2 = st.columns([3, 1])
    with p_header_col1:
        st.header("Single Employee Attrition Risk Predictor")
    with p_header_col2:
        st.button("🔄 Clear / Reset Form", on_click=reset_individual_form)

    st.markdown("Input employee parameters manually to generate immediate predictions, top SHAP risk drivers, and actionable HR advice. Labels marked with <span class='req-star'>*</span> are Mandatory Required Fields.", unsafe_allow_html=True)

    # Automatic Employee Data Lookup & Autofill Selector
    lookup_options = ["Custom New Input / Unlisted ID"] + registered_emp_ids
    selected_lookup_id = st.selectbox(
        "🔍 Select Existing Employee ID to Autofill Form Data:",
        lookup_options,
        index=0,
        help="Select an existing employee ID from the database to automatically fill all profile fields and load historical predictions!"
    )

    if selected_lookup_id != "Custom New Input / Unlisted ID":
        db = SessionLocal()
        try:
            d_service = DashboardService(db)
            emp_data = d_service.get_employee_by_id(selected_lookup_id)
            if emp_data:
                st.session_state["indiv_emp_id"] = emp_data["employee_id"]
                st.session_state["indiv_full_name"] = emp_data["full_name"]
                st.session_state["indiv_age"] = emp_data["age"]
                st.session_state["indiv_gender"] = emp_data["gender"]
                st.session_state["indiv_department"] = emp_data["department"]
                st.session_state["indiv_job_role"] = emp_data["job_role"]
                st.session_state["indiv_education_field"] = emp_data["education_field"]
                st.session_state["indiv_monthly_income"] = emp_data["monthly_income"]
                st.session_state["indiv_overtime"] = emp_data["overtime"]
                st.session_state["indiv_total_working_years"] = emp_data["total_working_years"]
                st.session_state["indiv_years_at_company"] = emp_data["years_at_company"]
                st.session_state["indiv_years_in_current_role"] = emp_data["years_in_current_role"]
                st.session_state["indiv_years_since_last_promotion"] = emp_data["years_since_last_promotion"]
                st.session_state["indiv_years_with_curr_manager"] = emp_data["years_with_curr_manager"]
                st.session_state["indiv_num_companies_worked"] = emp_data["num_companies_worked"]
                st.session_state["indiv_job_sat"] = emp_data["job_satisfaction"]

                # Automatically fetch latest prediction if available
                timeline = d_service.get_employee_history_timeline(selected_lookup_id)
                if timeline:
                    last_run = timeline[-1]
                    # Create mock result structure for rendering
                    class MockPredictionResult:
                        pass
                    m = MockPredictionResult()
                    m.attrition_probability = last_run["attrition_probability"]
                    m.attrition_prediction = 1 if last_run["attrition_probability"] >= 0.50 else 0
                    
                    class MockRiskLevel:
                        value = last_run["risk_level"]
                    m.risk_level = MockRiskLevel()

                    class MockFactor:
                        def __init__(self, f):
                            self.feature_name = f.get("feature_name", "N/A")
                            self.shap_value = f.get("shap_value", 0.0)
                            self.description = f.get("description", "N/A")
                    m.top_factors = [MockFactor(f) for f in last_run.get("top_factors", [])]

                    class MockRec:
                        def __init__(self, r):
                            self.category = r.get("category", "General")
                            self.title = r.get("title", "Recommendation")
                            self.action = r.get("action", "No action specified.")
                            self.priority = r.get("priority", "Low")
                    m.recommendations = [MockRec(r) for r in last_run.get("recommendations", [])]
                    st.session_state["individual_prediction_result"] = m
        finally:
            db.close()

    with st.form("prediction_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Demographics & Profile")
            st.markdown("Employee ID <span class='req-star'>*</span>", unsafe_allow_html=True)
            emp_id = st.text_input("emp_id_input", value=st.session_state["indiv_emp_id"], label_visibility="collapsed")
            
            st.markdown("Full Name", unsafe_allow_html=True)
            full_name = st.text_input("full_name_input", value=st.session_state["indiv_full_name"], label_visibility="collapsed")
            
            st.markdown("Age <span class='req-star'>*</span>", unsafe_allow_html=True)
            age = st.number_input("age_input", min_value=18, max_value=75, value=st.session_state["indiv_age"], label_visibility="collapsed")
            
            st.markdown("Gender", unsafe_allow_html=True)
            gender_options = ["Male", "Female"]
            gender_idx = gender_options.index(st.session_state["indiv_gender"]) if st.session_state["indiv_gender"] in gender_options else 0
            gender = st.selectbox("gender_input", gender_options, index=gender_idx, label_visibility="collapsed")

            st.markdown("Education Field", unsafe_allow_html=True)
            edu_options = ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"]
            edu_idx = edu_options.index(st.session_state["indiv_education_field"]) if st.session_state["indiv_education_field"] in edu_options else 0
            education_field = st.selectbox("edu_input", edu_options, index=edu_idx, label_visibility="collapsed")

        with col2:
            st.subheader("Work & Compensation")
            st.markdown("Department / Account <span class='req-star'>*</span>", unsafe_allow_html=True)
            dept_options = [
                "Research & Development", "Sales", "Human Resources",
                "CallCenter - Tech Support", "CallCenter - Customer Care",
                "CallCenter - Billing & Sales", "CallCenter - VIP Services",
                "CallCenter - Financial Support"
            ]
            dept_idx = dept_options.index(st.session_state["indiv_department"]) if st.session_state["indiv_department"] in dept_options else 0
            department = st.selectbox("department_input", dept_options, index=dept_idx, label_visibility="collapsed")
            
            st.markdown("Job Role <span class='req-star'>*</span>", unsafe_allow_html=True)
            role_options = [
                "Research Scientist", "Laboratory Technician", "Sales Executive",
                "Sales Representative", "Manufacturing Director", "Healthcare Representative",
                "Manager", "Human Resources", "Call Center Agent", "Customer Service Specialist",
                "Technical Support Representative", "Team Leader"
            ]
            role_idx = role_options.index(st.session_state["indiv_job_role"]) if st.session_state["indiv_job_role"] in role_options else 0
            job_role = st.selectbox("job_role_input", role_options, index=role_idx, label_visibility="collapsed")

            st.markdown("Monthly Income ($) <span class='req-star'>*</span>", unsafe_allow_html=True)
            monthly_income = st.number_input("income_input", min_value=100.0, max_value=50000.0, value=float(st.session_state["indiv_monthly_income"]), step=250.0, label_visibility="collapsed")
            
            st.markdown("Overtime Status <span class='req-star'>*</span>", unsafe_allow_html=True)
            ot_options = ["Yes", "No"]
            ot_idx = ot_options.index(st.session_state["indiv_overtime"]) if st.session_state["indiv_overtime"] in ot_options else 0
            overtime = st.selectbox("overtime_input", ot_options, index=ot_idx, label_visibility="collapsed")

            distance_from_home = 10
            business_travel = "Travel_Rarely"

        with col3:
            st.subheader("Tenure & Experience")
            st.markdown("Total Working Years <span class='req-star'>*</span>", unsafe_allow_html=True)
            total_working_years = st.number_input("working_years_input", min_value=0, max_value=50, value=st.session_state["indiv_total_working_years"], label_visibility="collapsed")
            
            st.markdown("Years at Company <span class='req-star'>*</span>", unsafe_allow_html=True)
            years_at_company = st.number_input("company_years_input", min_value=0, max_value=50, value=st.session_state["indiv_years_at_company"], label_visibility="collapsed")

            st.markdown("Years in Current Role", unsafe_allow_html=True)
            years_in_current_role = st.number_input("role_years_input", min_value=0, max_value=30, value=st.session_state["indiv_years_in_current_role"], label_visibility="collapsed")
            
            st.markdown("Years Since Last Promotion", unsafe_allow_html=True)
            years_since_last_promotion = st.number_input("promo_years_input", min_value=0, max_value=20, value=st.session_state["indiv_years_since_last_promotion"], label_visibility="collapsed")
            
            st.markdown("Years With Current Manager", unsafe_allow_html=True)
            years_with_curr_manager = st.number_input("mgr_years_input", min_value=0, max_value=20, value=st.session_state["indiv_years_with_curr_manager"], label_visibility="collapsed")
            
            st.markdown("Num Companies Worked", unsafe_allow_html=True)
            num_companies_worked = st.number_input("companies_input", min_value=0, max_value=15, value=st.session_state["indiv_num_companies_worked"], label_visibility="collapsed")

            st.markdown("Job Satisfaction (1-4) <span class='req-star'>*</span>", unsafe_allow_html=True)
            job_sat = st.slider("job_sat_slider", 1, 4, value=st.session_state["indiv_job_sat"], label_visibility="collapsed")

            env_sat = 3
            work_life = 3
            job_inv = 3
            perf_rating = 3

        submit_btn = st.form_submit_button("🚀 Generate AI Attrition Risk Analysis")

    if submit_btn:
        # Update Session State with submitted form inputs
        st.session_state["indiv_emp_id"] = emp_id.strip() if emp_id else ""
        st.session_state["indiv_full_name"] = full_name
        st.session_state["indiv_age"] = age
        st.session_state["indiv_gender"] = gender
        st.session_state["indiv_department"] = department
        st.session_state["indiv_job_role"] = job_role
        st.session_state["indiv_education_field"] = education_field
        st.session_state["indiv_monthly_income"] = monthly_income
        st.session_state["indiv_overtime"] = overtime
        st.session_state["indiv_total_working_years"] = total_working_years
        st.session_state["indiv_years_at_company"] = years_at_company
        st.session_state["indiv_years_in_current_role"] = years_in_current_role
        st.session_state["indiv_years_since_last_promotion"] = years_since_last_promotion
        st.session_state["indiv_years_with_curr_manager"] = years_with_curr_manager
        st.session_state["indiv_num_companies_worked"] = num_companies_worked
        st.session_state["indiv_job_sat"] = job_sat

        # Mandatory Validation Check
        missing_mandatory_fields = []
        if not emp_id or emp_id.strip() == "":
            missing_mandatory_fields.append("Employee ID")
        if age is None or age < 18:
            missing_mandatory_fields.append("Age")
        if not department:
            missing_mandatory_fields.append("Department")
        if not job_role:
            missing_mandatory_fields.append("Job Role")
        if monthly_income is None or monthly_income <= 0:
            missing_mandatory_fields.append("Monthly Income")
        if not overtime:
            missing_mandatory_fields.append("OverTime Status")
        if job_sat is None:
            missing_mandatory_fields.append("Job Satisfaction")
        if years_at_company is None:
            missing_mandatory_fields.append("Years at Company")
        if total_working_years is None:
            missing_mandatory_fields.append("Total Working Years")

        if missing_mandatory_fields:
            st.error(f"❌ Cannot process prediction! Missing required mandatory field(s): {', '.join(missing_mandatory_fields)}. Please fill in these required fields.")
        else:
            employee_payload = {
                "employee_id": emp_id.strip(),
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "department": department,
                "job_role": job_role,
                "education_field": education_field,
                "monthly_income": monthly_income,
                "distance_from_home": distance_from_home,
                "num_companies_worked": num_companies_worked,
                "total_working_years": total_working_years,
                "years_at_company": years_at_company,
                "years_in_current_role": years_in_current_role,
                "years_since_last_promotion": years_since_last_promotion,
                "years_with_curr_manager": years_with_curr_manager,
                "environment_satisfaction": env_sat,
                "job_satisfaction": job_sat,
                "work_life_balance": work_life,
                "job_involvement": job_inv,
                "performance_rating": perf_rating,
                "overtime": overtime,
                "business_travel": business_travel
            }

            db = SessionLocal()
            try:
                pred_service = PredictionService(db=db)
                result = pred_service.predict_single(employee_payload, save_to_db=True)
                st.session_state["individual_prediction_result"] = result
            finally:
                db.close()

    # Display Persisted Prediction Results if available in session_state
    result = st.session_state.get("individual_prediction_result")
    if result is not None:
        st.markdown("---")
        st.subheader("📌 AI Prediction Output")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Attrition Probability", f"{result.attrition_probability*100:.1f}%")
        with c2:
            st.markdown(f"**Risk Level:** {render_risk_badge(result.risk_level.value)}", unsafe_allow_html=True)
        with c3:
            prediction_text = "⚠️ Likely to Leave" if result.attrition_prediction == 1 else "✅ Likely to Stay"
            st.metric("Prediction Flag", prediction_text)

        st.markdown("---")

        col_xai, col_rec = st.columns([1, 1])

        with col_xai:
            st.subheader("🔍 Explainable AI (SHAP Factors)")
            factors_list = [
                {
                    "feature_name": f.feature_name,
                    "shap_value": f.shap_value,
                    "description": f.description
                }
                for f in result.top_factors
            ]
            shap_fig = create_shap_impact_chart(factors_list)
            st.plotly_chart(shap_fig, use_container_width=True)

        with col_rec:
            st.subheader("💡 Recommended HR Interventions")
            for rec in result.recommendations:
                priority_class = f"rec-card-{rec.priority.lower()}"
                st.markdown(f"""
                <div class="{priority_class}">
                    <div style="font-weight: 700; color: #F3F4F6;">[{rec.category}] {rec.title}</div>
                    <div style="font-size: 0.88rem; color: #D1D5DB; margin-top: 4px;">{rec.action}</div>
                    <div style="font-size: 0.78rem; color: #9CA3AF; margin-top: 4px;">Priority: <strong>{rec.priority}</strong></div>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# MODULE 3: BATCH PREDICTOR (WITH DYNAMIC HEIGHT & HIDDEN INDEX)
# ==============================================================================
elif menu == "📁 Batch Predictor":
    st.header("Bulk Batch Employee Predictor")
    st.caption("Upload a CSV or Excel file to process batch predictions. Rows missing mandatory fields will be skipped and reported.")

    uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])

    # Download Standard Sample Template Helper
    sample_v2_path = settings.BASE_DIR / "data" / "test_samples" / "omar_test_v2.xlsx"
    if sample_v2_path.exists():
        with open(sample_v2_path, "rb") as f:
            st.download_button(
                label="📥 Download Sample Batch Template (.xlsx)",
                data=f,
                file_name="sample_batch_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_input = pd.read_csv(uploaded_file)
            else:
                df_input = pd.read_excel(uploaded_file)

            st.write(f"Uploaded **{len(df_input)}** total employee rows. Scroll vertically or horizontally to inspect all uploaded records.")
            
            # Display full uploaded dataframe with dynamic height and hidden index column
            st.dataframe(
                df_input,
                height=get_table_height(df_input),
                hide_index=True,
                use_container_width=True
            )

            if st.button("🚀 Process Batch Prediction"):
                db = SessionLocal()
                try:
                    service = PredictionService(db=db)
                    batch_output = service.predict_batch(df_input, save_to_db=True)
                    
                    # Clean serialization to bulletproof dictionaries
                    raw_predictions = batch_output.get("predictions", [])
                    serialized_preds = []
                    for r in raw_predictions:
                        top_factors = getattr(r, "top_factors", [])
                        recs = getattr(r, "recommendations", [])
                        top_reason = top_factors[0].feature_name if top_factors and hasattr(top_factors[0], "feature_name") else "N/A"
                        top_rec = recs[0].title if recs and hasattr(recs[0], "title") else "N/A"
                        
                        r_level = getattr(r, "risk_level", "Low")
                        risk_str = r_level.value if hasattr(r_level, "value") else str(r_level)

                        serialized_preds.append({
                            "employee_id": str(getattr(r, "employee_id", "N/A")),
                            "attrition_probability": float(getattr(r, "attrition_probability", 0.0)),
                            "risk_level": risk_str,
                            "attrition_prediction": int(getattr(r, "attrition_prediction", 0)),
                            "primary_risk_driver": str(top_reason),
                            "recommended_action": str(top_rec)
                        })

                    st.session_state["batch_prediction_output"] = {
                        "predictions": serialized_preds,
                        "skipped_records": batch_output.get("skipped_records", [])
                    }
                finally:
                    db.close()

        except Exception as e:
            st.error(f"Error processing uploaded batch file: {str(e)}")

    # Display Persisted Batch Results & Analytics directly on the page
    batch_data = st.session_state.get("batch_prediction_output")
    if batch_data is not None:
        processed_list = batch_data.get("predictions", [])
        skipped_list = batch_data.get("skipped_records", [])

        st.markdown("---")

        # 1. Success Banner & KPI Summary Cards for this Batch
        if processed_list:
            st.success(f"✅ **Successfully processed & saved {len(processed_list)} complete employee records directly to SQL database!**")

            # Calculate Batch Metrics safely
            batch_probs = [float(r["attrition_probability"]) for r in processed_list]
            avg_batch_prob = sum(batch_probs) / len(batch_probs) if batch_probs else 0.0
            high_risk_count = sum(1 for r in processed_list if r["risk_level"] == "High")
            med_risk_count = sum(1 for r in processed_list if r["risk_level"] == "Medium")
            low_risk_count = sum(1 for r in processed_list if r["risk_level"] == "Low")

            # KPI Summary Cards
            b_c1, b_c2, b_c3, b_c4 = st.columns(4)
            with b_c1:
                render_kpi_card("Batch Processed", f"{len(processed_list):,}", "Saved to SQL", "#3B82F6", "👥")
            with b_c2:
                render_kpi_card("Avg Batch Risk", f"{avg_batch_prob*100:.1f}%", "Batch Risk Average", "#8B5CF6", "📈")
            with b_c3:
                render_kpi_card("High Risk Count", f"{high_risk_count:,}", "Immediate Action Needed", "#EF4444", "⚠️")
            with b_c4:
                render_kpi_card("Skipped Records", f"{len(skipped_list):,}", "Missing Mandatory Fields", "#F59E0B", "📋")

            st.markdown("---")

            # 2. Batch Risk Distribution Donut Chart
            c_donut, c_spacer = st.columns([1, 1])
            with c_donut:
                batch_donut = create_risk_distribution_chart(low_risk_count, med_risk_count, high_risk_count)
                st.plotly_chart(batch_donut, use_container_width=True)

            st.subheader("📊 Processed Employee Batch Results Roster")

            table_rows = []
            for r in processed_list:
                table_rows.append({
                    "Employee ID": r["employee_id"],
                    "Attrition Risk Probability (%)": f"{r['attrition_probability']*100:.1f}%",
                    "Risk Tier": r["risk_level"],
                    "Prediction Flag": "Leave" if r["attrition_prediction"] == 1 else "Stay",
                    "Primary Risk Driver": r["primary_risk_driver"],
                    "Recommended Action": r["recommended_action"]
                })

            res_df = pd.DataFrame(table_rows)
            st.dataframe(
                res_df,
                height=get_table_height(res_df),
                hide_index=True,
                use_container_width=True
            )

            # Export Download Button
            csv_bytes = res_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Processed Batch Results CSV",
                data=csv_bytes,
                file_name="attrition_batch_predictions.csv",
                mime="text/csv"
            )

        # 3. Skipped Records Warning & Audit Table
        if skipped_list:
            st.markdown("---")
            st.warning(f"⚠️ **{len(skipped_list)} record(s) skipped due to missing mandatory columns!**")
            skipped_df = pd.DataFrame([
                {
                    "Row Number": s["row_index"],
                    "Employee ID": s["employee_id"],
                    "Missing Mandatory Columns": ", ".join(s["missing_mandatory_columns"])
                }
                for s in skipped_list
            ])
            st.subheader("📋 Skipped Records Audit Table")
            st.dataframe(
                skipped_df,
                height=get_table_height(skipped_df),
                hide_index=True,
                use_container_width=True
            )

# ==============================================================================
# MODULE 4: AUDIT LOGS & EMPLOYEE HISTORICAL RISK TRAJECTORY INSPECTOR
# ==============================================================================
elif menu == "📜 Prediction Audit Logs":
    st.header("Prediction Audit Logs & Employee Trajectory Inspector")
    st.caption("Inspect historical predictions and track employee risk changes over time (Before vs. Now).")

    db = SessionLocal()
    try:
        dash_service = DashboardService(db)
        
        # ----------------------------------------------------------------------
        # SUB-SECTION: EMPLOYEE HISTORICAL TRAJECTORY INSPECTOR (BEFORE VS. NOW)
        # ----------------------------------------------------------------------
        st.subheader("📈 Employee Historical Risk Trajectory Inspector (Before vs. Now)")
        
        # Fetch list of registered employee IDs
        all_emps = dash_service.get_employees(limit=1000)
        emp_ids = [e["employee_id"] for e in all_emps] if all_emps else ["CC-AGENT-001"]

        selected_emp_id = st.selectbox("Select Employee ID to Inspect Trajectory:", emp_ids, index=0)

        if selected_emp_id:
            timeline_records = dash_service.get_employee_history_timeline(selected_emp_id)
            if timeline_records:
                # Plot Trajectory Line Chart
                timeline_fig = create_employee_risk_timeline_chart(timeline_records, selected_emp_id)
                st.plotly_chart(timeline_fig, use_container_width=True)

                # Before vs. Now Metric Cards
                first_run = timeline_records[0]
                latest_run = timeline_records[-1]

                t1, t2, t3 = st.columns(3)
                with t1:
                    st.metric("Initial Risk Score (Before)", f"{first_run['attrition_probability']*100:.1f}%", help=f"Recorded at {first_run['created_at']}")
                with t2:
                    delta_risk = round((latest_run['attrition_probability'] - first_run['attrition_probability']) * 100, 1)
                    st.metric("Current Risk Score (Now)", f"{latest_run['attrition_probability']*100:.1f}%", delta=f"{delta_risk}%", delta_color="inverse")
                with t3:
                    st.markdown(f"**Current Status:** {render_risk_badge(latest_run['risk_level'])}", unsafe_allow_html=True)

                st.subheader(f"Detailed Prediction History Runs for {selected_emp_id}")
                
                hist_records_df = pd.DataFrame(timeline_records)[["prediction_id", "attrition_probability", "risk_level", "created_at"]].copy()
                hist_records_df["attrition_probability"] = (hist_records_df["attrition_probability"] * 100).apply(lambda x: f"{x:.1f}%")
                hist_records_df = hist_records_df.rename(columns={
                    "prediction_id": "Prediction ID",
                    "attrition_probability": "Attrition Risk Probability (%)",
                    "risk_level": "Risk Tier",
                    "created_at": "Analysis Timestamp"
                })
                st.dataframe(
                    hist_records_df,
                    height=get_table_height(hist_records_df),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info(f"No historical prediction runs logged for employee ID '{selected_emp_id}' yet.")

        st.markdown("---")

        # ----------------------------------------------------------------------
        # SUB-SECTION: GLOBAL PREDICTION AUDIT LOGS TABLE
        # ----------------------------------------------------------------------
        st.subheader("📋 All System Prediction Audit Logs")
        history_records = dash_service.get_prediction_history(limit=200)

        if history_records:
            hist_df = pd.DataFrame(history_records).copy()
            # Format probabilities as clean percentages XX.X%
            hist_df["attrition_probability"] = (hist_df["attrition_probability"] * 100).apply(lambda x: f"{x:.1f}%")
            
            # Clean human-readable column headers (No Underscores)
            hist_df = hist_df.rename(columns={
                "prediction_id": "Prediction ID",
                "employee_id": "Employee ID",
                "employee_name": "Employee Name",
                "department": "Department / Account",
                "job_role": "Job Role",
                "attrition_probability": "Attrition Risk Probability (%)",
                "risk_level": "Risk Tier",
                "created_at": "Analysis Timestamp"
            })
            
            st.dataframe(
                hist_df[["Prediction ID", "Employee ID", "Employee Name", "Department / Account", "Job Role", "Attrition Risk Probability (%)", "Risk Tier", "Analysis Timestamp"]],
                height=get_table_height(history_records),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No prediction history logged in database yet.")

    finally:
        db.close()
