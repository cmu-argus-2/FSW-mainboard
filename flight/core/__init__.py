# Core modules containing the framework of the flight software
from core.logging import logger, setup_logger
from core.state_machine import StateManager
from core.template_task import TemplateTask

# expose the Singleton state manager
state_manager = StateManager()
