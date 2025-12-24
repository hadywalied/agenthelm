"""OpenTelemetry tracing integration for AgentHelm."""

from contextlib import contextmanager
from typing import Any, Generator
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: trace.Tracer | None = None
_initialized = False


def init_tracing(
    service_name: str = "agenthelm",
    otlp_endpoint: str = "http://localhost:4317",
    enabled: bool = True,
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing with OTLP export (Jaeger-compatible).

    Args:
        service_name: Name to identify this service in Jaeger
        otlp_endpoint: OTLP gRPC endpoint (Jaeger default: localhost:4317)
        enabled: If False, returns a no-op tracer

    Returns:
        Configured tracer instance
    """
    global _tracer, _initialized

    if _initialized:
        return _tracer

    if not enabled:
        _tracer = trace.get_tracer(service_name)
        _initialized = True
        return _tracer

    # Configure resource (service metadata)
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.3.0",
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter for Jaeger
    try:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        logger.info(f"OpenTelemetry initialized: exporting to {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"Failed to configure OTLP exporter: {e}")

    # Set as global provider
    trace.set_tracer_provider(provider)

    _tracer = trace.get_tracer(service_name)
    _initialized = True

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the current tracer (initializes with defaults if needed)."""
    global _tracer
    if _tracer is None:
        return init_tracing(enabled=False)  # No-op by default
    return _tracer


@contextmanager
def trace_tool(
    tool_name: str,
    inputs: dict[str, Any] | None = None,
    agent_name: str | None = None,
) -> Generator[trace.Span, None, None]:
    """
    Context manager for tracing tool execution.

    Usage:
        with trace_tool("search", inputs={"query": "AI news"}) as span:
            result = search(query)
            span.set_attribute("result_count", len(result))
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(tool_name) as span:
        # Set standard attributes
        span.set_attribute("tool.name", tool_name)
        if agent_name:
            span.set_attribute("agent.name", agent_name)
        if inputs:
            for key, value in inputs.items():
                span.set_attribute(f"input.{key}", str(value)[:256])

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


@contextmanager
def trace_agent(
    agent_name: str,
    task: str,
) -> Generator[trace.Span, None, None]:
    """
    Context manager for tracing agent execution (parent span).

    Usage:
        with trace_agent("researcher", task="Find AI news") as span:
            result = agent.run(task)
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(f"agent:{agent_name}") as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("agent.task", task[:512])

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def shutdown():
    """Flush and shutdown the tracer provider."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()
