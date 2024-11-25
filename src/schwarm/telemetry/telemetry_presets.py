from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.models.event import EventType
from schwarm.telemetry.sqlite_telemetry_exporter import SqliteTelemetryExporter

cfg = TelemetryConfig()

cfg.break_on_events = [EventType.START_TURN, EventType.POST_TOOL_EXECUTION]
cfg.log_on_events = [EventType.START]

DEFAULT_SQL_TELEMETRY = [SqliteTelemetryExporter(cfg)]
