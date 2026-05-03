from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PipelineState:
    last_run: datetime | None = None
    is_running: bool = False
    articles_processed: int = 0


pipeline_state = PipelineState()
