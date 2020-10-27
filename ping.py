from aiohttp import web
import asyncio

from helpers import get_tracing_client, tracing_method, tracer_middleware, fetch
from rpc.rpc_client import FibonacciRpcClient


tracing_client = get_tracing_client(service_name="ping.py")


@tracing_method
async def test_sleep(t):
    await asyncio.sleep(t)


async def ping_handler(request):
    pong = await fetch("http://localhost:8082")

    await test_sleep(0.1)
    await asyncio.sleep(0.1)

    fibonacci_rpc = FibonacciRpcClient()
    fib = fibonacci_rpc.call(30)

    return web.json_response({'ping': pong, 'fib': fib})


def init():
    app = web.Application(
        middlewares=[
            tracer_middleware,
        ]
    )
    app.router.add_get("/", ping_handler)
    return app


if __name__ == "__main__":
    web.run_app(init(), port=8080)
