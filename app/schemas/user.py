from pydantic import field_validator, BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import re

# ─── Profile ──────────────────────────────────────────────────────────────────

class UpdateProfile(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    profile_picture_url: Optional[str] = None
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Full name must be less than 100 characters")
        return v
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v is None:
            return v
        if v not in["male", "female", "other"]:
            raise ValueError("Gender must be male, female or other")
        return v

class UpdatePhone(BaseModel):
    phone: str
    otp: str
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError("Enter a valid 10 digit Indian mobile number")
        return v

class UpdateEmail(BaseModel):
    email: EmailStr
    password: str

class AddressCreate(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"
    address_type: str = "home"
    is_default: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError("Enter a valid 10 digit Indian mobile number")
        return v
    
    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v):
        if not re.match(r'\d{6}$', v):
            raise ValueError("Pincode must be 6 digits")
        return
    
    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, v):
        if v not in ["home", "work", "other"]:
            raise ValueError("Address type must be home, work or other")
        return v
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v

class AddressUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    address_type: Optional[str] = None
    is_default: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError("Enter a valid 10 digit Indian mobile number")
        return v

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{6}$', v):
            raise ValueError("Pincode must be 6 digits")
        return v


# ─── Responses ────────────────────────────────────────────────────────────────

class AddressResponse(BaseModel):
    id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str
    address_type: str
    is_default: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    profile_picture_url: Optional[str] = None
    is_verified: bool
    is_phone_verified: bool
    flipkart_plus: bool
    created_at: datetime
    addresses: List[AddressResponse] = []

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}