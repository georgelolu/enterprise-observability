import logging
import os

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    Counter,
    Histogram,
    make_asgi_app,
)
from pythonjsonlogger.json import JsonFormatter

service_name = "product-service"

logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter("%(levelname)s %(name)s %(message)s"))

logger = logging.getLogger(service_name)
logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False

resource = Resource.create({
    "service.name": service_name,
    "deployment.environment.name": os.getenv(
        "DEPLOYMENT_ENV", "development"
    ),
})

provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_ENDPOINT",
                "http://localhost:4317",
            ),
            insecure=True,
        )
    )
)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(service_name)

app = FastAPI(title="Product Service")

# Application-level HTTP metrics for Prometheus.
HTTP_REQUESTS = Counter(
    "product_service_http_requests_total",
    "Total HTTP requests handled by the Product Service.",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "product_service_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "endpoint"],
)

@app.middleware("http")
async def collect_http_metrics(request, call_next):
    # Do not count Prometheus scrapes as application traffic.
    if request.url.path.startswith("/metrics"):
        return await call_next(request)

    import time

    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    route = request.scope.get("route")
    endpoint = getattr(route, "path", "unmatched")
    method = request.method
    status_code = str(response.status_code)

    HTTP_REQUESTS.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)

    return response

app.mount("/metrics", make_asgi_app())

products = {
    "101": {"id": "101", "name": "Laptop", "price": 1200},
    "102": {"id": "102", "name": "Keyboard", "price": 80},
}


@app.get("/health")
def health():
    return {"status": "healthy", "service": service_name}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/products/{product_id}")
def get_product(product_id: str):
    with tracer.start_as_current_span("product.lookup") as span:
        span.set_attribute("product.id", product_id)

        product = products.get(product_id)
        if product is None:
            span.set_attribute("error.type", "not_found")
            logger.warning(
                "product_not_found",
                extra={"product_id": product_id},
            )
            raise HTTPException(
                status_code=404,
                detail="Product not found",
            )

        logger.info(
            "product_lookup_success",
            extra={"product_id": product_id},
        )
        return product


FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
