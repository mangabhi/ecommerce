from pydantic import BaseModel,Field
from decimal import Decimal

class ChatMessage(BaseModel):
    role: str
    content: str


class ShoppingAssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list)

class RecommendedProduct(BaseModel):
    id:int
    name:str
    description:str | None=None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    image_url:str | None =None 
    category_name:str | None =None
    reason:str 

class ShoppingAssistantResponse(BaseModel):
    message: str
    products: list[RecommendedProduct]


