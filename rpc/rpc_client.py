import pika
import uuid

from helpers import tracing_method, get_tracing_client


class FibonacciRpcClient:
    def __init__(self):
        self.tracing_client = get_tracing_client("rpc_client.py")

        credentials = pika.PlainCredentials('user', 'bitnami')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='answer', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(on_message_callback=self.on_response, auto_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    @tracing_method
    def call(self, n):
        self.response = None
        self.corr_id = self.get_corr_id()

        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n)
        )
        while self.response is None:
            self.connection.process_data_events()
        return int(self.response)

    def get_corr_id(self):
        import opentracing
        span = opentracing.tracer.active_span

        from opentracing import tags
        span.set_tag(tags.HTTP_METHOD, 'GET FROM RABBIT')
        span.set_tag(tags.HTTP_URL, "FibonacciRpcClient")
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        headers = {}
        from opentracing import Format
        opentracing.tracer.inject(span, Format.HTTP_HEADERS, headers)

        return headers.get('uber-trace-id') or str(uuid.uuid4())


if __name__ == "__main__":
    fibonacci_rpc = FibonacciRpcClient()
    print(" [x] Requesting fib(30)")
    response = fibonacci_rpc.call(30)
    print(" [.] Got %r" % response)

    print(" [x] Requesting fib(10)")
    response = fibonacci_rpc.call(10)
    print(" [.] Got %r" % response)
