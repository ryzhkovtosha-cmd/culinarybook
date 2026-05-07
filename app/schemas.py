from typing import List

from pydantic import BaseModel, ConfigDict, Field


class RecipeCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Оливье"})
    cooking_time: int = Field(..., gt=0, json_schema_extra={"example": 60})
    ingredients: List[str] = Field(
        ...,
        json_schema_extra={"example": ["картофель", "морковь",
                                       "горошек", "майонез"]},
    )
    description: str = Field(
        ..., json_schema_extra={"example": "Классический салат..."}
    )


class RecipeDetail(RecipeCreate):
    id: int
    views: int
    model_config = ConfigDict(from_attributes=True)


class RecipeListItem(BaseModel):
    name: str
    views: int
    cooking_time: int
    model_config = ConfigDict(from_attributes=True)
