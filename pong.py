from aiohttp import web
import asyncio

from helpers import tracing_method, tracer_middleware
from helpers import get_tracing_client

tracing_client = get_tracing_client(service_name="pong.py")


@tracing_method
async def test_sleep(t):
    await asyncio.sleep(t)


async def pong_handler(request):
    await test_sleep(0.1)
    return web.json_response({'message': 'pong'})


def init():
    app = web.Application(
        middlewares=[
            tracer_middleware,
        ]
    )
    app.router.add_get("/", pong_handler)
    return app


if __name__ == "__main__":
    web.run_app(init(), port=8082)
