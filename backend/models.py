from pydantic import BaseModel, Field, field_validator
from typing import Optional

class RadiolineInput(BaseModel):
    Ptx: float = Field(..., description="Power of source signal [dB]")
    Gtx: float = Field(..., description="Gain of transmitter [dB]")
    Grx: float = Field(..., description="Gain of receiver [dB]")
    d: float = Field(..., gt=0, description="Distance between tx and rx [km]")
    f: float = Field(..., gt=0, description="Signal frequency [GHz]")
    rain_density: Optional[str] = Field(None, description="Rain density [mm per hour]")
    
    @field_validator('Ptx', 'Gtx', 'Grx')
    def validate_power(cls, v):
        return v
    
    @field_validator('d')
    def validate_distance(cls, v):
        if v > 0:
            return v
        else:
            raise ValueError(f'Distance must be > 0, got {v}')
        
    
    @field_validator('f')
    def validate_frequency(cls, v):
        if v > 0:
            return v
        else:
            raise ValueError(f'Frequency must be > 0, got {v}')
    
    @field_validator('rain_density')
    def validate_rain_density(cls, v):
        if v is None or v == 'None':
            return None
        allowed_values = ['0', '5', '25', '50', '100', '150', '200']
        if v not in allowed_values:
            raise ValueError(f'Rain density must be one of {allowed_values}, got {v}')
        return v

class RadiolineResult(BaseModel):
    RSSI: float
    FSPL: float
    rain_attenuation: float
    atmosphere_attenuation: float