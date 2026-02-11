from inspection.framework import InspectionPipeline, InspectionContext
from inspection.plugins import HTTPInspector, DNSInspector, SMTPInspector

# Initialize pipeline
pipeline = InspectionPipeline()

# Register inspectors
pipeline.register_plugin(HTTPInspector())
pipeline.register_plugin(DNSInspector())
pipeline.register_plugin(SMTPInspector())

# Inspect HTTP traffic
context = InspectionContext(
    src_ip="192.0.2.1",
    dst_ip="93.184.216.34",
    src_port=45678,
    dst_port=80,
    protocol="TCP",
    direction="outbound",
    flow_id="flow_abc123",
    timestamp=time.time(),
    metadata={}
)

http_request = b"GET /../../etc/passwd HTTP/1.1\r\nHost: example.com\r\n\r\n"

result = pipeline.inspect(context, http_request)

if result.is_blocked:
    print(f"🚫 BLOCKED!")
    for finding in result.findings:
        print(f"  - {finding.severity}: {finding.description}")
else:
    print("✅ ALLOWED")

# Statistics
stats = pipeline.get_statistics()
print(f"Total inspections: {stats['total_inspections']}")
print(f"Block rate: {stats['block_rate']:.2f}%")
print(f"Avg processing time: {stats['avg_processing_time_ms']:.2f}ms")
