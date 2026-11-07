from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from core.export import text_to_pdf
from ..deps import rate_limit

router = APIRouter(dependencies=[Depends(rate_limit)])


class ExportIn(BaseModel):
    title: str = Field(default="Draft", max_length=120)
    text: str = Field(min_length=1, max_length=20000)


@router.post("/export")
def export_pdf(body: ExportIn):
    return Response(content=text_to_pdf(body.text, body.title), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="draft.pdf"'})
