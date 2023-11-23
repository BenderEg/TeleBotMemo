import logging

from core.config import settings

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=settings.log_level)