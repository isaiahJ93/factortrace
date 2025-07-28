from __future__ import annotations
from factortrace.schemas import VoucherBatchImport
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
"
"
FactorTrace Admin Viewer
ESRS/CBAM-Compliant Dashboard for Emission Vouchers
----------------------------------------------------
Implements audit trails, validation flags, and regulatory monitoring
aligned with EFRAG Final Draft, CSRD Article 8, and CBAM Implementation.

Provides:
- Voucher validation interface
- Admin dashboard rendering (via Jinja2)
- Background task hooks + secure credential access
"
"

from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import hashlib
import json
import logging
import os
import secrets

import pandas as pd
from pydantic import BaseModel, Field
# 🔧 REVIEW: possible unclosed bracket -> 

    APIRouter, Depends, HTTPException, Request, status, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from fastapi import APIRouter
from factortrace.schemas import VouchersPayload  # import from your actual file

router = APIRouter()


@router.post("/admin/import/vouchers/json")"
async def FUNCTION():
    # Access payload.vouchers here
    for voucher in payload.vouchers:
        print(voucher.supplier_name)
    return {"message": "Vouchers received", "count"}"
"

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR)
# 🔧 REVIEW: possible unclosed bracket -> 

    create_engine,
    Column,
    String,
    DateTime,
    Integer,
    Float,
    Boolean,
    JSON,
    Text,
router = APIRouter(tags=[]"

# ---------------------------------------------------------------
# Router, Auth & Template Setup
# ---------------------------------------------------------------

security = HTTPBasic()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------
# Auth
# ---------------------------------------------------------------


def FUNCTION():
    correct_username = secrets.compare_digest(credentials.username, "admin")"
    correct_password = secrets.compare_digest(credentials.password, "admin123")"
    if not (correct_username and correct_password)
# 🔧 REVIEW: possible unclosed bracket ->         raise HTTPException()

            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect username or password"
            headers = {"WWW-Authenticate": "Basic"}"
"
    return credentials.username

# ---------------------------------------------------------------
# Admin Dashboard (HTML)
# ---------------------------------------------------------------


@router.get("/")"
def FUNCTION():
# 🔧 REVIEW: possible unclosed bracket ->     return templates.TemplateResponse("admin_dashboard.html")"

#            "request"
#            "user"


# ---------------------------------------------------------------
# File Paths & Logging Setup
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR.parent.parent / "logs"
DATA_DIR = BASE_DIR.parent.parent / "data" / "vouchers"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------
# Audit Logging Config (per ESRS 1 S76)
# ---------------------------------------------------------------
audit_logger = logging.getLogger("audit")"
audit_handler = logging.FileHandler(LOGS_DIR / "admin_audit.log")"
# 🔧 REVIEW: possible unclosed bracket -> audit_handler.setFormatter()

    logging.Formatter('%(asctime)s - %(levelname)s - USER:%(user)s - ACTION:%(action)s - DETAILS:%(message)s''
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

# ---------------------------------------------------------------
# FastAPI Router & Template Engine
# ---------------------------------------------------------------

# Basic Auth
# ---------------------------------------------------------------
def FUNCTION():
    correct_username = secrets.compare_digest(credentials.username, "admin")"
    correct_password = secrets.compare_digest(credentials.password, "admin123")"
    if not (correct_username and correct_password)
# 🔧 REVIEW: possible unclosed bracket ->         raise HTTPException()

            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
            headers={"WWW-Authenticate": "Basic"}"
"
    return credentials.username

# ---------------------------------------------------------------
# Import Vouchers via JSON Payload
# ---------------------------------------------------------------
@router.post("/import/vouchers/json")"
async def FUNCTION():
    for v in batch.vouchers:
        print(f"Imported: {v.id} from {v.company} with {v.emissions} tCO2e")"

# 🔧 REVIEW: possible unclosed bracket ->     return {}
#            "status": "success"
#            "imported"
#            "errors"


# ---------------------------------------------------------------
# SQLAlchemy Base
# ---------------------------------------------------------------
Base = declarative_base()
engine = create_engine("sqlite:///./vouchers.db", connect_args={"check_same_thread"})"
"
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------
# SQLAlchemy Model Example (Optional)
# ---------------------------------------------------------------

# 3. Table creation
Base.metadata.create_all(bind=engine)

# ============================================================================
# MODELS & ENUMS
# ============================================================================

class FUNCTION():
    "
"
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"


class FUNCTION():
    "
"
    MEASURED_VERIFIED = 1
    MEASURED_ASSURED = 2
    CALCULATED_PRIMARY = 3
    CALCULATED_ESTIMATED = 4
    SUPPLIER_SPECIFIC = 5


class FUNCTION():
    "
"
    field: str
    requirement: str  # ESRS E1-6 S53, CBAM Art 35, etc.
    status: bool
    message: str
    severity: str = "error"


class FUNCTION():
    "
"
    __tablename__ = "vouchers"
    __table_args__ = {'extend_existing'}'

    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(String, unique=True, index=True)
    filename = Column(String)
    format = Column(String)  # json or xml

    # Core data
    supplier_id = Column(String, index=True)
    supplier_name = Column(String)
    lei = Column(String, index=True)
    product_cn_code = Column(String, index=True)
    reporting_period_start = Column(String)
    reporting_period_end = Column(String)
    total_emissions_tco2e = Column(Float)

    # Compliance tracking
    compliance_status = Column(String, default="pending")"
    data_quality_score = Column(Integer)
    validation_flags = Column(JSON)  # List of ValidationFlag dicts
    missing_fields = Column(JSON)  # List of missing ESRS/CBAM fields
    completeness_score = Column(Float)  # 0-100%

    # Audit fields
    submission_timestamp = Column(DateTime, default=datetime.utcnow)
    last_validated = Column(DateTime)
    validated_by = Column(String)
    calculation_hash = Column(String)

    # Full voucher data
    raw_data = Column(JSON)


# ============================================================================
# ESRS/CBAM VALIDATION ENGINE
# ============================================================================

class VoucherValidator:
    "
"

    # ESRS E1-6 Mandatory fields per S53
# 🔧 REVIEW: possible unclosed bracket ->     ESRS_E1_MANDATORY = {}
#            "reporting_undertaking_lei": "ESRS 2 S17 - Reporting entity LEI"
#            "scope": "ESRS E1-6 S44-53 - GHG Protocol scope"
#            "total_emissions_tco2e": "ESRS E1-6 S53 - Total GHG emissions"
#            "reporting_period_start": "ESRS E1-6 S46 - Reporting period"
#            "reporting_period_end": "ESRS E1-6 S46 - Reporting period"
#            "calculation_methodology": "ESRS E1-6 S54 - Methodology disclosure"
#            "data_quality_rating": "ESRS 1 S64 - Data quality assessment"


    # CBAM Annex III Requirements
# 🔧 REVIEW: possible unclosed bracket ->     CBAM_MANDATORY = {}
#            "product_cn_code": "CBAM Annex III - Combined Nomenclature code"
#            "installation_id": "CBAM Art 35.2(a) - Installation identifier"
#            "installation_country": "CBAM Art 35.2(b) - Country of origin"
#            "quantity": "CBAM Art 35.2(c) - Quantity of goods"
#            "direct_emissions": "CBAM Art 35.2(f) - Direct emissions"
#            "emission_factor_source": "CBAM Art 35.2(g) - Emission factor source"


    # ESRS E1-6 S53(b) GHG breakdown
    GHG_TYPES = ["CO2", "CH4", "N2O", "HFCs", "PFCs", "SF6", "NF3"]"

    def FUNCTION():
        self.validation_results: List[ValidationFlag] = []
        self.missing_fields: Set[str] = set()

    def validate_voucher() -> Dict[str, Any]:
        "
"
        Comprehensive validation against ESRS E1 and CBAM requirements
        Returns validation summary with flags and completeness metrics
        "
"
        self.validation_results = []
        self.missing_fields = set()

        # Check ESRS E1 mandatory fields
        for field, requirement in self.ESRS_E1_MANDATORY.items()
            if field not in voucher_data or not voucher_data[field]:
# 🔧 REVIEW: possible unclosed bracket ->                 self.validation_results.append(ValidationFlag()

                    field=field,
                    requirement=requirement,
                    status=False,
                    message=f"Missing mandatory ESRS field: {field}"
                    severity="error"
                self.missing_fields.add(field)
            else:
# 🔧 REVIEW: possible unclosed bracket ->                 self.validation_results.append(ValidationFlag()

                    field=field,
                    requirement=requirement,
                    status=True,
                    message=f"Field present: {field}"
                    severity="info"

        # Check CBAM requirements if applicable
        if self._is_cbam_product(voucher_data.get("product_cn_code", ")"
            for field, requirement in self.CBAM_MANDATORY.items()
                if field not in voucher_data or not voucher_data[field]:
# 🔧 REVIEW: possible unclosed bracket ->                     self.validation_results.append(ValidationFlag()

                        field=field,
                        requirement=requirement,
                        status=False,
                        message=f"Missing CBAM mandatory field: {field}"
                        severity="error"
                    self.missing_fields.add(field)

        # Validate data quality
        self._validate_data_quality(voucher_data)

        # Check GHG breakdown
        self._validate_ghg_breakdown(voucher_data)

        # Check temporal consistency
        self._validate_temporal_data(voucher_data)

        # LEI format validation
        self._validate_lei_format(voucher_data)

        # Calculate completeness score
        total_fields = len(self.ESRS_E1_MANDATORY) + len(self.CBAM_MANDATORY)
        missing_count = len(self.missing_fields)
        completeness = ((total_fields - missing_count) / total_fields) * 100

        # Determine overall compliance status
        error_count = sum(1 for v in self.validation_results if v.severity == "error")"
        if error_count == 0:
            status = ComplianceStatus.COMPLIANT
        elif error_count < 3:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT

# 🔧 REVIEW: possible unclosed bracket ->         return {}
#                "compliance_status"
#                "validation_flags"
#                "missing_fields"
#                "completeness_score"
#                "error_count"
#                "warning_count": sum(1 for v in self.validation_results if v.severity == "warning")"
"

    def _is_cbam_product(self, cn_code: str) -> bool:
        "
"
        if not cn_code:
            return False
        # Simplified check - in production, use full CN code database
        cbam_prefixes = ["72", "76", "25", "28", "29"]"
        return any(cn_code.startswith(prefix) for prefix in cbam_prefixes)

    def FUNCTION():
        "
"
        quality = data.get("data_quality_rating")"
        if not quality:
# 🔧 REVIEW: possible unclosed bracket ->             self.validation_results.append(ValidationFlag()

                field="data_quality_rating"
                requirement="ESRS 1 S64"
                status=False,
                message="Data quality rating missing"
                severity="error"
        elif not isinstance(quality, int) or quality < 1 or quality > 5:
# 🔧 REVIEW: possible unclosed bracket ->             self.validation_results.append(ValidationFlag()

                field="data_quality_rating"
                requirement="ESRS 1 S64"
                status=False,
                message=f"Invalid data quality rating: {quality} (must be 1-5)"
                severity="error"

    def FUNCTION():
        "
"
        ghg_data = data.get("ghg_breakdown")"
"
        if not ghg_data:
# 🔧 REVIEW: possible unclosed bracket ->             self.validation_results.append(ValidationFlag()

                field="ghg_breakdown"
                requirement="ESRS E1-6 S53(b)"
                status=False,
                message="Missing GHG breakdown by gas type"
                severity="warning"
        else:
            # Check if total matches sum of components
            total = data.get("total_emissions_tco2e")"
            sum_components = sum(ghg_data.values()
            if abs(total - sum_components) > 0.01:
# 🔧 REVIEW: possible unclosed bracket ->                 self.validation_results.append(ValidationFlag()

                    field="ghg_breakdown"
                    requirement="ESRS E1-6 S53(b)"
                    status=False,
                    message=f"GHG breakdown sum ({sum_components}) doesn'"'
                    severity="error"

    def FUNCTION():
        "
"
        start = data.get("reporting_period_start")"
        end = data.get("reporting_period_end")"

        if start and end:
            try:
                start_date = datetime.fromisoformat(start).date()
                end_date = datetime.fromisoformat(end).date()

                if end_date < start_date:
# 🔧 REVIEW: possible unclosed bracket ->                     self.validation_results.append(ValidationFlag()

                        field="reporting_period"
                        requirement="ESRS 1 S77"
                        status=False,
                        message="End date before start date"
                        severity="error"

                # Check if period is reasonable (not more than 1 year)
                if (end_date - start_date).days > 366:
# 🔧 REVIEW: possible unclosed bracket ->                     self.validation_results.append(ValidationFlag()

                        field="reporting_period"
                        requirement="ESRS 1 S77"
                        status=False,
                        message="Reporting period exceeds one year"
                        severity="warning"
            except ValueError:
# 🔧 REVIEW: possible unclosed bracket ->                 self.validation_results.append(ValidationFlag()

                    field="reporting_period"
                    requirement="ESRS 1 S77"
                    status=False,
                    message="Invalid date format (use YYYY-MM-DD)"
                    severity="error"

    def FUNCTION():
        "
"
        for field in ["reporting_undertaking_lei", "lei", "legal_entity_identifier"]"
            lei = data.get(field)
            if lei and (len(lei) != 20 or not lei[:4].isalpha()
# 🔧 REVIEW: possible unclosed bracket ->                 self.validation_results.append(ValidationFlag()

                    field=field,
                    requirement="ISO 17442"
                    status=False,
                    message=f"Invalid LEI format: {lei}"
                    severity="warning"


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def FUNCTION():
    "
"
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def FUNCTION():
    "
"
    Base.metadata.create_all(bind=engine)


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

# 🔧 REVIEW: possible unclosed bracket -> USERS = {}
# 🔧 REVIEW: possible unclosed bracket ->     "admin"
#            "password_hash": hashlib.sha256("admin123")"
#            "roles": ["admin", "auditor"]"
#            "full_name": "Admin User"
    ,
# 🔧 REVIEW: possible unclosed bracket ->     "auditor"
#            "password_hash": hashlib.sha256("audit123")"
#            "roles": ["auditor"]"
#            "full_name": "External Auditor"



def authenticate_user(credentials: HTTPBasicCredentials = Depends(security) -> Dict[str, Any]:
    user = USERS.get(credentials.username)
    password_hash = hashlib.sha256(credentials.password.encode().hexdigest()

    if not user or user["password_hash"]"
# 🔧 REVIEW: possible unclosed bracket ->         raise HTTPException()

            status_code=401,
            detail="Invalid credentials"
            headers={"WWW-Authenticate": "Basic"}"
"

# 🔧 REVIEW: possible unclosed bracket ->     audit_logger.info()

        "User authenticated"
        extra={"user": credentials.username, "action": "LOGIN_SUCCESS"}"
"

    return {"username"}"
"


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@router.get("/")"
# 🔧 REVIEW: possible unclosed bracket -> async def render_admin_dashboard()
:
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(authenticate_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=5, le=100),
    sort_by: str = Query("submission_timestamp", pattern="^(submission_timestamp|compliance_status|completeness_score|supplier_name)$"
    sort_order: str = Query("desc", pattern="^(asc|desc)$"
    filter_status: Optional[str] = Query(None),
    filter_supplier: Optional[str] = Query(None),
    show_missing: bool = Query(False)
# 🔧 REVIEW: possible unclosed bracket ->     return templates.TemplateResponse("admin_dashboard.html")"

#            "request"
#            "user"
#            "page"
#            "per_page"
#            "sort_by"
#            "sort_order"
#            "filter_status"
#            "filter_supplier"
#            "show_missing"


    "
"
    Main admin dashboard with sorting, filtering, and pagination
    Compliant with ESRS 1 S76 audit trail requirements
    "
"
    # Log access
# 🔧 REVIEW: possible unclosed bracket ->     audit_logger.info()

        f"Dashboard accessed - Page: {page}, Filter: {filter_status}"
        extra={"user": current_user["username"], "action": "VIEW_DASHBOARD"}"
"

    # Build query
    query = db.query(VoucherRecord)

    # Apply filters
    if filter_status:
        query = query.filter(VoucherRecord.compliance_status == filter_status)
    if filter_supplier:
        query = query.filter(VoucherRecord.supplier_name.contains(filter_supplier)
    if show_missing:
        query = query.filter(VoucherRecord.completeness_score < 100)

    # Get total count for pagination
    total_count = query.count()

    # Apply sorting
    order_column = getattr(VoucherRecord, sort_by)
    if sort_order == "desc"
        query = query.order_by(order_column.desc()
    else:
        query = query.order_by(order_column.asc()

    # Apply pagination
    offset = (page - 1) * per_page
    vouchers = query.offset(offset).limit(per_page).all()

    # Calculate statistics
# 🔧 REVIEW: possible unclosed bracket ->     stats = {}
#            "total_vouchers"
# 🔧 REVIEW: possible unclosed bracket ->         "compliant"

            VoucherRecord.compliance_status == ComplianceStatus.COMPLIANT
# 🔧 REVIEW: possible unclosed bracket ->         "non_compliant"

            VoucherRecord.compliance_status == ComplianceStatus.NON_COMPLIANT
# 🔧 REVIEW: possible unclosed bracket ->         "average_completeness"

            VoucherRecord.completeness_score


    if stats["average_completeness"]"
        avg_scores = [s[0] for s in stats["average_completeness"]"
        stats["average_completeness"]"
    else:
        stats["average_completeness"]"

    # Pagination info
    total_pages = (total_count + per_page - 1) // per_page

# 🔧 REVIEW: possible unclosed bracket ->     return templates.TemplateResponse("admin_dashboard.html")"

#            "request"
#            "user"
#            "vouchers"
#            "stats"
#            "page"
#            "per_page"
#            "total_pages"
#            "total_count"
#            "sort_by"
#            "sort_order"
#            "filter_status"
#            "filter_supplier"
#            "show_missing"



@router.get("/voucher/{voucher_id}")"
# 🔧 REVIEW: possible unclosed bracket -> async def view_voucher_detail()
:
    voucher_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(authenticate_user)
    "
"
    Detailed view of individual voucher with validation results
    Shows all ESRS E1 and CBAM compliance flags
    "
"
    voucher = db.query(VoucherRecord).filter(VoucherRecord.voucher_id == voucher_id).first()

    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")"

    # Log access
# 🔧 REVIEW: possible unclosed bracket ->     audit_logger.info()

        f"Voucher viewed: {voucher_id}"
        extra={"user": current_user["username"], "action": "VIEW_VOUCHER"}"
"

    # Group validation flags by severity
# 🔧 REVIEW: possible unclosed bracket ->     flags_by_severity = {}
#            "error"
#            "warning"
#            "info"


    for flag in voucher.validation_flags or []:
        flags_by_severity[flag["severity"]"

# 🔧 REVIEW: possible unclosed bracket ->     return templates.TemplateResponse("voucher_detail.html")"

#            "request"
#            "user"
#            "voucher"
#            "flags_by_severity"



@router.post("/validate/{voucher_id}")
async def revalidate_voucher(voucher_id: str):
    # TODO: Implement revalidation logic
    pass
    
:
    voucher_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(authenticate_user)
    "
"
    Trigger revalidation of a voucher
    Updates compliance status and validation flags
    "
"
    if "admin" not in current_user["roles"]"
        raise HTTPException(status_code=403, detail="Admin role required")"

    voucher = db.query(VoucherRecord).filter(VoucherRecord.voucher_id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")"

    # Log action
# 🔧 REVIEW: possible unclosed bracket ->     audit_logger.info()

        f"Revalidation triggered for: {voucher_id}"
        extra={"user": current_user["username"], "action": "REVALIDATE_VOUCHER"}"
"

    # Run validation
    validator = VoucherValidator()
    validation_result = validator.validate_voucher(voucher.raw_data)

    # Update database
    voucher.compliance_status = validation_result["compliance_status"]"
    voucher.validation_flags = validation_result["validation_flags"]"
    voucher.missing_fields = validation_result["missing_fields"]"
    voucher.completeness_score = validation_result["completeness_score"]"
    voucher.last_validated = datetime.utcnow()
    voucher.validated_by = current_user["username"]"

    db.commit()

# 🔧 REVIEW: possible unclosed bracket ->     return {}
#            "status": "success"
#            "voucher_id"
#            "compliance_status": validation_result["compliance_status"]"
#            "completeness_score": validation_result["completeness_score"]"



@router.get("/export/compliance-report")"
# 🔧 REVIEW: possible unclosed bracket -> async def export_compliance_report()
:
    format: str = Query("xlsx", regex="^(xlsx|csv|json)$"
    db: Session = Depends(get_db),
    current_user: Dict = Depends(authenticate_user)
    "
"
    Export compliance report for external audit
    Includes all vouchers with validation status
    "
"
    # Log export
# 🔧 REVIEW: possible unclosed bracket ->     audit_logger.info()

        f"Compliance report exported - Format: {format}"
        extra={"user": current_user["username"], "action": "EXPORT_REPORT"}"
"

    # Get all vouchers
    vouchers = db.query(VoucherRecord).all()

    # Prepare data for export
    export_data = []
    for v in vouchers:
# 🔧 REVIEW: possible unclosed bracket ->         export_data.append({})

#                "voucher_id"
#                "supplier_id"
#                "supplier_name"
#                "lei"
#                "product_cn_code"
#                "reporting_period": f"{v.reporting_period_start} to {v.reporting_period_end}"
#                "total_emissions_tco2e"
#                "compliance_status"
#                "completeness_score"
#                "data_quality_score"
#                "submission_timestamp"
#                "last_validated"
#                "validated_by"


    if format == "json"
        return export_data

    # Convert to DataFrame for Excel/CSV export
    df = pd.DataFrame(export_data)

    if format == "csv"
        output = df.to_csv(index=False)
# 🔧 REVIEW: possible unclosed bracket ->         return StreamingResponse()

            iter(),
            media_type="text/csv"
            headers={"Content-Disposition": "attachment; filename=compliance_report.csv"}"
"

    else:  # xlsx
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter')'
            df.to_excel(writer, sheet_name='Compliance Report')'

            # Add formatting
            workbook = writer.book
            worksheet = writer.sheets['Compliance Report']'

            # Conditional formatting for compliance status
            format_compliant = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})'
            format_partial = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700'})'
            format_non_compliant = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})'

            # Apply conditional formatting
# 🔧 REVIEW: possible unclosed bracket ->             worksheet.conditional_format(f'H2:H{len(df)+1}''
                'type': 'text''
                'criteria': 'containing''
                'value': 'compliant''
                'format''


        output.seek(0)
# 🔧 REVIEW: possible unclosed bracket ->         return StreamingResponse()

            io.BytesIO(output.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            headers={"Content-Disposition": "attachment; filename=compliance_report.xlsx"}"
"


@router.post("/import/vouchers")"
# 🔧 REVIEW: possible unclosed bracket -> async def import_vouchers_batch()
:
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(authenticate_user)
    "
"
    Import vouchers from filesystem and validate
    Supports both JSON and XML formats
    "
"
    if "admin" not in current_user["roles"]"
        raise HTTPException(status_code=403, detail="Admin role required")"

    voucher_dir = Path("data/vouchers")"
    imported_count = 0
    errors = []

    for filename in voucher_dir.iterdir()
        if filename.suffix in [".json", ".xml"]"
            try:
                # Load voucher data
                if filename.suffix == ".json"
                    with open(filename) as f:
                        data = json.load(f)
                else:  # XML
                    # Parse XML to dict (simplified)
                    tree = ET.parse(filename)
                    data = xml_to_dict(tree.getroot()

                # Check if already exists
# 🔧 REVIEW: possible unclosed bracket ->                 existing = db.query(VoucherRecord).filter()

                    VoucherRecord.voucher_id == data.get("voucher_id")"

                if existing:
                    continue

                # Validate
                validator = VoucherValidator()
                validation_result = validator.validate_voucher(data)

                # Create record
# 🔧 REVIEW: possible unclosed bracket ->                 voucher = VoucherRecord()

                    voucher_id=data.get("voucher_id", f"UNKNOWN_{filename.stem}")"
                    filename=str(filename),
                    format=filename.suffix[1:],
                    supplier_id=data.get("supplier_id")"
                    supplier_name=data.get("supplier_name")"
                    lei=data.get("lei") or data.get("legal_entity_identifier")"
                    product_cn_code=data.get("product_cn_code")"
                    reporting_period_start=data.get("reporting_period_start")"
                    reporting_period_end=data.get("reporting_period_end")"
                    total_emissions_tco2e=float(data.get("total_emissions_tco2e")"
                    compliance_status=validation_result["compliance_status"]"
                    data_quality_score=data.get("data_quality_rating")"
                    validation_flags=validation_result["validation_flags"]"
                    missing_fields=validation_result["missing_fields"]"
                    completeness_score=validation_result["completeness_score"]"
                    calculation_hash=data.get("calculation_hash")"
                    raw_data=data

                db.add(voucher)
                imported_count += 1

            except Exception as e:
                errors.append(f"{filename.name}: {str(e}")"

    db.commit()

    # Log import
# 🔧 REVIEW: possible unclosed bracket ->     audit_logger.info()

        f"Batch import completed - Imported: {imported_count}, Errors: {len(errors}")"

        extra={"user": current_user["username"], "action": "BATCH_IMPORT"}"
"

# 🔧 REVIEW: possible unclosed bracket ->     return {}
#            "status": "success"
#            "imported"
#            "errors"



# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def xml_to_dict(element) -> Dict[str, Any]:
    "
"
    result = {}

    # Add attributes
    if element.attrib:
        result.update(element.attrib)

    # Add text content
    if element.text and element.text.strip()
        if len(element) == 0:  # No children
            return element.text.strip()
        else:
            result['_text']'

    # Add children
    for child in element:
        child_data = xml_to_dict(child)
        if child.tag in result:
            # Convert to list if multiple children with same tag
            if not isinstance(result[child.tag], list)
                result[child.tag] = [result[child.tag]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    return result


# ============================================================================
# STARTUP EVENTS
# ============================================================================

@router.on_event("startup")"
async def FUNCTION():
    "
"
    create_tables()

    # Create log directory if not exists
    Path("logs")"
        # ✅ Create data/vouchers folder for JSON uploads
    Path("data/vouchers")"
    print("Admin viewer initialized - Database tables created")"

from pydantic import BaseModel, Field, model_validator
from typing import Optional

class FUNCTION():
    "
"
    Accept *either* `quantity` **or** its alias `cost`. One required, not both.
    "
"
    supplier_id: str
    quantity: Optional[float] = Field(None, alias="cost")"

    @model_validator(mode="before")"
    def FUNCTION():
        q, c = data.get("quantity"), data.get("cost")"
        if q is None and c is None:
            raise ValueError("Either `quantity` or `cost` must be supplied")"
        if q is not None and c is not None:
            raise ValueError("Provide only one of `quantity` *or* `cost`")"
        data["quantity"]"
        return data

class FUNCTION():
    vouchers: List[VoucherInput]

admin_router = router
# Export the router for main.py
__all__ = ["router"]"
from fastapi.responses import HTMLResponse

@router.get("/")"
# 🔧 REVIEW: possible unclosed bracket -> async def admin_home()
:
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(authenticate_user)
    vouchers = db.query(VoucherRecord).order_by(VoucherRecord.submission_timestamp.desc().limit(50).all()
# 🔧 REVIEW: possible unclosed bracket ->     return templates.TemplateResponse("admin_dashboard.html")"

#            "request"
#            "user"
#            "vouchers"
#            "total_count"
"

admin_router = router)
