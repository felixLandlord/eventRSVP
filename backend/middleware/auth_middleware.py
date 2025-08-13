# from typing import Callable, Any
# from backend.services.auth_service import AuthService
#
#
# async def auth_middleware(resolver: Callable, obj: Any, info, **args) -> Any:
#     """
#     Runs for every GraphQL request:
#     - Extracts Bearer token from Authorization header
#     - Validates token
#     - Fetches current user from DB
#     - Injects `token` and `current_user` into context
#     """
#     request = info.context.get("request")
#     token = None
#     current_user = None
#
#     if request:
#         auth_header = request.headers.get("Authorization")
#         if auth_header and auth_header.startswith("Bearer "):
#             token = auth_header.split(" ", 1)[1]
#
#     info.context["token"] = token
#
#     if token:
#         try:
#             current_user = await AuthService.get_current_user(token)
#         except Exception:
#             current_user = None
#
#     info.context["current_user"] = current_user
#
#     return await resolver(obj, info, **args)
