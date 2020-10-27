import opentracing
from aiohttp import ClientSession
from aiohttp.web_middlewares import middleware
from jaeger_client import Config
from opentracing import Format, tags


def get_tracing_client(service_name):
    config = Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "local_agent": {
                "reporting_host": "localhost",
                "reporting_port": "5775"
            },
            'logging': True,
            'reporter_batch_size': 1,
        },
        service_name=service_name,
    )
    return config.initialize_tracer()


def tracing_method(func):
    def wrapper(*args, **kwargs):
        with opentracing.tracer.start_active_span(func.__name__, finish_on_close=True):
            return func(*args, **kwargs)
    return wrapper


@middleware
async def tracer_middleware(request, handler):
    span_ctx = opentracing.tracer.extract(Format.HTTP_HEADERS, request.headers)
    span_tags = {
        tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER,
        tags.HTTP_METHOD: request.method,
    }
    with opentracing.tracer.start_active_span(handler.__name__, child_of=span_ctx, tags=span_tags):
        return await handler(request)


@tracing_method
async def fetch(url):
    span = opentracing.tracer.active_span
    span.set_tag(tags.HTTP_METHOD, 'GET')
    span.set_tag(tags.HTTP_URL, url)
    span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
    headers = {}
    opentracing.tracer.inject(span, Format.HTTP_HEADERS, headers)

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
    return data
