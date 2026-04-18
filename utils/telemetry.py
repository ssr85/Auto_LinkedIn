import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

def init_tracing(service_name: str = "auto-linkedin"):
    """
    Initializes OpenTelemetry tracing.
    Currently configured for console-only output as a structured flight recorder.
    Can be upgraded to OTLP (Jaeger/Honeycomb) by switching the exporter.
    """
    provider = TracerProvider()
    
    # ConsoleSpanExporter prints structured spans to stdout/stderr
    # which will be captured in the logs.
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    print(f"--- TELEMETRY: Tracing initialized for {service_name} (Console) ---")

def get_tracer(module_name: str):
    """
    Returns a tracer instance for the specified module.
    """
    return trace.get_tracer(module_name)
