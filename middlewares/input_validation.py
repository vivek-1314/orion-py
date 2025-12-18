from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

MAX_INPUT_LEN = 250

class InputValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path == "/run-graph":
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid JSON body."}
                )

            user_input = body.get('input', '').strip()
            user_id = body.get('user_id', '').strip()

            # Empty or missing fields
            if not user_input or not user_id:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Missing required field: 'input' or 'user_id'."}
                )

            # Max length
            if len(user_input) > MAX_INPUT_LEN:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Input too long. Max length is {MAX_INPUT_LEN} characters."}
                )

            request.state.user_input = user_input
            request.state.user_id = user_id

        # Continue to route
        response = await call_next(request)
        return response
