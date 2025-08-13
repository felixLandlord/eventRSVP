# import strawberry
# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from strawberry.asgi import GraphQL
# from contextlib import asynccontextmanager
#
# from backend.core.config import settings
# from backend.core.database import db
# from backend.graphql_api.query import Query
# from backend.graphql_api.mutation import Mutation
# from backend.graphql_api.context import get_context_value
# from typing import Any
#
#
# class CustomGraphQL(GraphQL):
#     async def get_context(self, request: Any, response: Any) -> Any:
#         return await get_context_value(request)
#
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await db.create_all()
#     print("🚀 Database initialized successfully!")
#     yield
#     await db.close()
#     print("📁 Database connection closed!")
#
#
# def create_app() -> FastAPI:
#     schema = strawberry.Schema(query=Query, mutation=Mutation)
#
#     app = FastAPI(
#         title="🎉 Event Management & RSVP Platform",
#         description="A modern event management platform with RSVP functionality",
#         version="1.0.0",
#         docs_url="/docs",
#         redoc_url="/redoc",
#         lifespan=lifespan,
#     )
#
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#
#     app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
#
#     @app.get("/")
#     async def root():
#         return {
#             "message": "🎉 Welcome to Event Management Platform API!",
#             "status": "healthy",
#             "graphql_endpoint": "/graphql",
#         }
#
#     @app.get("/health")
#     async def health_check():
#         return {"status": "healthy", "timestamp": "2025-01-10T16:08:32Z"}
#
#     graphql_app = CustomGraphQL(
#         schema,
#         graphiql=True,
#         multipart_uploads_enabled=True,
#     )
#     app.mount("/graphql", graphql_app)
#
#     return app
#
#
# app = create_app()
#
# if __name__ == "__main__":
#     uvicorn.run(
#         "backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
#     )

import strawberry
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager

from backend.core.config import settings
from backend.core.database import db
from backend.graphql_api.query import Query
from backend.graphql_api.mutation import Mutation
from backend.graphql_api.context import get_context_value
from backend.core.limiter import setup_rate_limiting


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_all()
    print("🚀 Database initialized successfully!")
    yield
    await db.close()
    print("📁 Database connection closed!")


def create_app() -> FastAPI:
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    app = FastAPI(
        title="🎉 Event Management & RSVP Platform",
        description="A modern event management platform with RSVP functionality",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    # Health endpoints
    @app.get("/")
    async def root():
        return {
            "message": "🎉 Welcome to Event Management Platform API!",
            "status": "healthy",
            "graphql_endpoint": "/graphql",
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    # GraphQL router with context
    graphql_app = GraphQLRouter(
        schema,
        context_getter=get_context_value,  # ensures request is passed
        graphiql=True,
    )
    app.include_router(graphql_app, prefix="/graphql")

    # Setup rate limiting
    setup_rate_limiting(app)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
