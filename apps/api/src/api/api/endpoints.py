from fastapi import FastAPI, Request, APIRouter
from api.api.models import RAGRequest,RAGResponse, RAGUsedContext
from api.agents.graph import rag_agent_wrapper
from api.api.processors import submit_feedback
from api.api.models import FeedbackRequest, FeedbackResponse
from api.api.processors.submit_feedback import submit_feedback


import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


rag_router= APIRouter()
feedback_router= APIRouter()

@rag_router.post("/")
def rag(
    request: Request,
    payload:RAGRequest
) -> RAGResponse:
    answer= rag_agent_wrapper(payload.query,payload.thread_id )

    return RAGResponse(
        request_id=request.state.request_id,
        answer =answer["answer"],
        used_context=[RAGUsedContext(**used_context) for used_context in answer["used_context"]],
        trace_id=answer["trace_id"]
    )

@feedback_router.post("/")
def send_feedback(
    request: Request,
    payload: FeedbackRequest
) -> FeedbackResponse:
    submit_feedback(payload.trace_id, payload.feedback_score, payload.feedback_text, payload.feedback_source_type)
    return FeedbackResponse(
        request_id=request.state.request_id,
        status="success"
    )

api_router=APIRouter()
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(feedback_router, prefix="/submit_feedback", tags=["feedback"])

