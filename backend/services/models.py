from sqlalchemy import (
    Column,
    String,
    Boolean,
    TIMESTAMP,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

# 1) ENUM type for ingredient/scan verdicts
class ScanVerdictEnum(str, enum.Enum):
    safe = "safe"
    potentially_unsafe = "potentially unsafe"
    unsafe = "unsafe"


# 2) Users table
class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")


# 3) Master list of dietary restrictions
class DietaryRestriction(Base):
    __tablename__ = "dietary_restrictions"

    restriction_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    name = Column(String, unique=True, nullable=False)


# 4) (Optional) Users' default dietary preferences
#    You can drop this if you don’t need per-user defaults,
#    since each scan records its own restriction list.
class UserDietaryPreference(Base):
    __tablename__ = "user_dietary_preferences"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    restriction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietary_restrictions.restriction_id", ondelete="CASCADE"),
        primary_key=True,
    )


# 5) Scans table
class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    s3_image_url = Column(String, nullable=False)
    final_verdict = Column(
        SAEnum(ScanVerdictEnum, name="scan_verdict"), nullable=False
    )
    scanned_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")


# 6) Join table: which restriction(s) were used for each scan
class ScanDietaryRestriction(Base):
    __tablename__ = "scan_dietary_restrictions"

    scan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scans.scan_id", ondelete="CASCADE"),
        primary_key=True,
    )
    restriction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietary_restrictions.restriction_id", ondelete="CASCADE"),
        primary_key=True,
    )


# 7) Ingredients extracted per scan (with per-ingredient verdict and trace flag)
class ScanIngredient(Base):
    __tablename__ = "scan_ingredients"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    scan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scans.scan_id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_name = Column(String, nullable=False)
    verdict = Column(SAEnum(ScanVerdictEnum, name="scan_verdict"), nullable=False)
    is_trace = Column(Boolean, default=False)


# 8) Password reset tokens (for completeness)
class PasswordReset(Base):
    __tablename__ = "password_resets"

    reset_id = Column(
        UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    used = Column(Boolean, default=False)
