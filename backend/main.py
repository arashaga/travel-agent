import os
import asyncio
from turtle import ht
from fastapi import FastAPI, HTTPException, Header, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import sys
import uuid
import re




# Ensure imports work both when run as module (python -m backend.main)
# and as a script (python backend/main.py)
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

# Local imports
from backend.services.agents import TravelConversationManagerFactory
from backend.settings.instructions import COORDINATOR_AGENT_NAME, FLIGHT_AGENT_NAME, HOTEL_AGENT_NAME
from backend.settings.logging import get_logger
logger = get_logger("travel.api")

class ChatRequest(BaseModel):
    message: str
    reset: bool | None = False
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str


def create_app() -> FastAPI:
    # Load environment variables from cwd and backend/.env for robustness
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parent / ".env")

    app = FastAPI(title="Travel Agent API", version="0.1.0")

    # CORS (liberal by default; tighten as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # One conversation manager shared per-process (simple state)
    manager = TravelConversationManagerFactory.create()

    # --- API key authentication ---
    expected_api_key = os.getenv("TRAVEL_AGENT_API_KEY")

    async def verify_api_key(
        authorization: str | None = Header(default=None, alias="Authorization"),
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> bool:
        """Simple API key check.
        Accepts either Authorization: Bearer <key> or X-API-Key: <key>.
        The expected key must be set in TRAVEL_AGENT_API_KEY environment variable.
        """
        if not expected_api_key:
            logger.error("TRAVEL_AGENT_API_KEY is not set; refusing request")
            raise HTTPException(status_code=500, detail="Server API key not configured")

        provided_key = None
        if authorization and authorization.lower().startswith("bearer "):
            provided_key = authorization.split(" ", 1)[1].strip()
        elif x_api_key:
            provided_key = x_api_key.strip()

        if not provided_key or provided_key != expected_api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        return True

    def _sanitize_agent_output(text: str) -> str:
        """Remove internal agent-process chatter and keep a concise, user-facing message."""
        if not text:
            return text
        
        text = re.sub(r"^\*\*[^*]+\*\*:\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\[ *delegate:.*?\]\s*", "", text, flags=re.IGNORECASE)
        # Remove bracketed agent tags like [FlightSpecialist], [HotelSpecialist]
        # Use simple replacements for known agent names
        for tag in (FLIGHT_AGENT_NAME, HOTEL_AGENT_NAME, COORDINATOR_AGENT_NAME):
            text = re.sub(rf"\[\s*{re.escape(tag)}\s*\]", "", text)

        # Drop lines that look like internal process chatter
        drop_keywords = [
            "delegate to",
            "delegating to",
            "handoff",
            "hand off",
            "invoking",
            "invoke",
            "plugin",
            "tool call",
            "agent group",
            "coordinator will",
        ]
        cleaned_lines = []
        # State: skip content following section headers like '### Flights' or '### Hotels' until a blank line
        skip_section = False
        for line in text.splitlines():
            s = line.strip()
            # End skipping at blank line
            if skip_section and s == "":
                skip_section = False
                continue
            # Skip content while in a section skip
            if skip_section:
                continue
            # Start skipping if we hit a section header
            l = s.lower()
            if l.startswith("### Flights") or l.startswith("### Hotels"):
                skip_section = True
                continue
            if not s:
                cleaned_lines.append("")
                continue
            if s.lower().startswith("understood:"):
                continue
            if any(k in s.lower() for k in drop_keywords):
                continue
            cleaned_lines.append(s)

        # collapse extra blanks
        out, prev_blank = [], False
        for l in cleaned_lines:
            blank = (l == "")
            if blank and prev_blank:
                continue
            out.append(l); prev_blank = blank
        return "\n".join(out).strip()

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(
        req: ChatRequest,
        request: Request,
        response: Response,
        x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
        _authorized: bool = Depends(verify_api_key),
    ):
        req_id = str(uuid.uuid4())[:8]
        # Derive session id from (1) header, (2) body, (3) cookie, otherwise create and set cookie
        session_id = x_session_id or req.session_id or request.cookies.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax", path="/")

        logger.info(
            "[%s] /api/chat start session=%s reset=%s msg=%r",
            req_id, session_id, req.reset, req.message
        )
        if req.reset:
            manager.reset_conversation(session_id)
        try:
            responses = await manager.send_message(session_id, req.message, verbose=False)
            # Prefer the coordinator's last message if present; fall back to last message
            #name_and_text = []
            latest_by_name = {}
            names = []
            pattern = re.compile(r"^\*\*(.+?)\*\*:\s*(.*)$", re.DOTALL)
            for r in responses:
                logger.debug("[%s] RAW_AGENT: %s", req_id, (r[:1000] + "…") if len(r) > 1000 else r)
                m = pattern.match(r)
                if m:
                    
                    name, text = m.group(1), m.group(2)
                    latest_by_name[name] = text
                    print("name: ", name, "text: ",  text)
                    names.append(name)
                else:
                    names.append("Unknown")
            logger.info("[%s] agent replies=%d from=%s", req_id, len(responses), names)

            # Always prefer only the coordinator's latest message to keep a single clear response
            coord = latest_by_name.get(COORDINATOR_AGENT_NAME)
            if coord:
                combined = coord.strip()
            else:
                # Fallback to last message text if coordinator is absent
                if responses:
                    last = responses[-1]
                    m = pattern.match(last)
                    combined = (m.group(2) if m else last).strip()
                else:
                    combined = ""
            final_text = _sanitize_agent_output(combined)
            logger.info(
                "[%s] final response: coord_present=%s bytes=%d",
                req_id,
                bool(coord),
                len(final_text.encode("utf-8"))
            )
            logger.debug("[%s] final preview: %s", req_id, (final_text[:500] + "…") if len(final_text) > 500 else final_text)
            
            return ChatResponse(response=final_text)

        #     final_text = ""
        #     for name, text in reversed(name_and_text):
        #         if name == COORDINATOR_AGENT_NAME:
        #             final_text = text
        #             break
        #     if not final_text:
        #         # Fallback: aggregate latest flight and hotel specialist outputs if available
        #         latest_flight = None
        #         latest_hotel = None
        #         for name, text in name_and_text:
        #             if name == FLIGHT_AGENT_NAME:
        #                 latest_flight = text
        #             elif name == HOTEL_AGENT_NAME:
        #                 latest_hotel = text
        #         parts = []
        #         if latest_flight:
        #             parts.append("Flights:\n" + _sanitize_agent_output(latest_flight))
        #         if latest_hotel:
        #             parts.append("Hotels:\n" + _sanitize_agent_output(latest_hotel))
        #         if parts:
        #             final_text = "\n\n".join(parts)
        #         elif name_and_text:
        #             final_text = name_and_text[-1][1]
        #     return ChatResponse(response=_sanitize_agent_output(final_text))
        except Exception as e:
            logger.exception("[%s] /api/chat failure", req_id)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health():
        return {"status": "ok", "build": "coord-only-v2"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
