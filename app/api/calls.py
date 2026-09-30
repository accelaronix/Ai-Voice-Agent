from fastapi import APIRouter
from pydantic import BaseModel

from app.telephony.exotel import (
    start_outbound_call
)


router = APIRouter(
    prefix="/calls",
    tags=["Calls"]
)


class TestCallRequest(
    BaseModel
):
    phone: str


@router.post("/test")
def test_call(
    data: TestCallRequest
):

    stream_url = (
        "wss://decisions-raymond-aware-predictions."
        "trycloudflare.com/"
        "voice/media?sample-rate=16000"
    )

    result = start_outbound_call(
        phone=data.phone,
        stream_url=stream_url
    )

    return result