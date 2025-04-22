from pydantic import BaseModel
from typing import List


class ROIColor(BaseModel):
    id: int
    r: int
    g: int
    b: int


class ROIData(BaseModel):
    data: List[ROIColor]
