from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import Literal

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    @field_validator('name', check_fields=False)
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError('Name must contain visible characters only')
        return value
class ProjectInput(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=2000)
class ImportInput(StrictModel):
    upload_id: str
    project_id: str
    name: str = Field(min_length=1, max_length=120)
    mapping: dict[str, str] = Field(default_factory=dict)
    time_unit: Literal['s', 'ms', 'ns'] = 's'
    gyro_unit: Literal['rad/s', 'deg/s'] = 'rad/s'
    source: str = Field(default='User recording', max_length=500)
    segment: int | None = Field(default=None, ge=0)
class Outage(StrictModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    @model_validator(mode='after')
    def ordered(self):
        if self.end <= self.start: raise ValueError('Outage end must follow start')
        return self
class RunInput(StrictModel):
    project_id: str
    dataset_id: str
    name: str = Field(default='Navigation experiment', min_length=1, max_length=120)
    outages: list[Outage] = Field(default_factory=list, max_length=50)
    model_id: str | None = None
    calibration_id: str | None = None
    accel_noise: float = Field(default=0.3, ge=0.001, le=10)
    gyro_noise: float = Field(default=0.02, ge=0.0001, le=1)
    gps_noise: float = Field(default=5, ge=0.1, le=100)
    initial_heading_deg: float | None = Field(default=None, ge=0, lt=360)
    initial_speed_mps: float | None = Field(default=None, ge=0, le=100)
    initial_lat: float | None = Field(default=None, ge=-85, le=85)
    initial_lng: float | None = Field(default=None, ge=-180, le=180)
    mount_yaw_deg: float = Field(default=0, ge=-180, le=180)
class TrainInput(StrictModel):
    project_id: str
    name: str = Field(default='Velocity model', min_length=1, max_length=120)
    train_ids: list[str] = Field(min_length=1)
    validation_ids: list[str] = Field(min_length=1)
    test_ids: list[str] = Field(min_length=1)
    architecture: Literal['ridge', 'cnn_gru'] = 'ridge'
    epochs: int = Field(default=20, ge=1, le=200)
    seed: int = Field(default=42, ge=0, le=2147483647)
    @model_validator(mode='after')
    def disjoint(self):
        groups = [set(self.train_ids), set(self.validation_ids), set(self.test_ids)]
        if any(groups[i] & groups[j] for i in range(3) for j in range(i+1,3)):
            raise ValueError('Train, validation, and test recordings must be disjoint')
        return self
class CalibrationInput(StrictModel):
    project_id: str
    dataset_id: str
    name: str = Field(default='Stationary calibration', min_length=1, max_length=120)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
class PairInput(StrictModel):
    code: str = Field(min_length=6, max_length=80)
    name: str = Field(min_length=1, max_length=100)
class BatchInput(StrictModel):
    version: Literal[1] = 1
    session_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
    sequence: int = Field(ge=0)
    samples: list[dict[str, float | None]] = Field(min_length=1, max_length=1000)
    metadata: dict = Field(default_factory=dict)
class RecordOut(BaseModel):
    id: str
    kind: str
    project_id: str | None
    name: str
    data: dict
    created_at: str
class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
class JobOut(BaseModel):
    id: str
    project_id: str
    kind: str
    status: str
    progress: int
    message: str
    config: dict
    result_id: str | None
    created_at: str
    updated_at: str
