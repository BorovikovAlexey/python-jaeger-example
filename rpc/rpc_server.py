import opentracing
import pika
from opentracing import Format, tags

from helpers import get_tracing_client

tracing_client = get_tracing_client(service_name="rpc_server.py")

credentials = pika.PlainCredentials('user', 'bitnami')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
channel = connection.channel()

channel.queue_declare(queue='rpc_queue')


def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)


def on_request(ch, method, props, body):
    headers = {
        'uber-trace-id': props.correlation_id,
    }
    span_ctx = opentracing.tracer.extract(Format.HTTP_HEADERS, headers)
    span_tags = {
        tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER,
        tags.HTTP_METHOD: 'answer ',
    }
    with opentracing.tracer.start_active_span('rpc answer', child_of=span_ctx, tags=span_tags):
        n = int(body)

        print(" [.] fib(%s)" % n)
        response = fib(n)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=str(response)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == "__main__":
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_message_callback=on_request, queue='rpc_queue')

    print(" [x] Awaiting RPC requests")
    channel.start_consuming()
