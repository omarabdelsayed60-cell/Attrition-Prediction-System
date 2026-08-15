from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

class User(Base):
    """ORM Model representing system users and HR managers."""
    __tablename__ = "Users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="HR_Manager", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class Employee(Base):
    """ORM Model representing employee profile and demographics."""
    __tablename__ = "Employees"

    employee_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    department: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    job_role: Mapped[str] = mapped_column(String(50), nullable=False)
    education_field: Mapped[str] = mapped_column(String(50), nullable=False)
    monthly_income: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    distance_from_home: Mapped[int] = mapped_column(Integer, nullable=False)
    num_companies_worked: Mapped[int] = mapped_column(Integer, nullable=False)
    total_working_years: Mapped[int] = mapped_column(Integer, nullable=False)
    years_at_company: Mapped[int] = mapped_column(Integer, nullable=False)
    years_in_current_role: Mapped[int] = mapped_column(Integer, nullable=False)
    years_since_last_promotion: Mapped[int] = mapped_column(Integer, nullable=False)
    years_with_curr_manager: Mapped[int] = mapped_column(Integer, nullable=False)
    environment_satisfaction: Mapped[int] = mapped_column(Integer, nullable=False)
    job_satisfaction: Mapped[int] = mapped_column(Integer, nullable=False)
    work_life_balance: Mapped[int] = mapped_column(Integer, nullable=False)
    job_involvement: Mapped[int] = mapped_column(Integer, nullable=False)
    performance_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    overtime: Mapped[str] = mapped_column(String(5), nullable=False)
    business_travel: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="employee", cascade="all, delete-orphan")

class Prediction(Base):
    """ORM Model representing single prediction execution logs."""
    __tablename__ = "Predictions"

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("Employees.employee_id", ondelete="SET NULL"), nullable=True, index=True)
    attrition_probability: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    attrition_prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    employee: Mapped[Optional["Employee"]] = relationship("Employee", back_populates="predictions")
    history_record: Mapped[Optional["PredictionHistory"]] = relationship("PredictionHistory", back_populates="prediction", uselist=False, cascade="all, delete-orphan")

class PredictionHistory(Base):
    """ORM Model storing detailed SHAP factors and generated HR recommendations in JSON format."""
    __tablename__ = "PredictionHistory"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey("Predictions.prediction_id", ondelete="CASCADE"), nullable=False)
    top_risk_factors_json: Mapped[str] = mapped_column(Text, nullable=False)
    hr_recommendations_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="history_record")
