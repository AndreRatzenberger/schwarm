from schwarm.core.schwarm import Schwarm
from schwarm.models.agent import Agent
from schwarm.provider.provider_presets import DEFAULT
from schwarm.telemetry.telemetry_presets import DEFAULT_SQL_TELEMETRY

hello_agent = Agent(name="hello_agent", configs=DEFAULT)
Schwarm(telemetry_exporters=DEFAULT_SQL_TELEMETRY).quickstart(hello_agent)
