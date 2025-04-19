import logging
from django import template

register = template.Library()
LOGGER=logging.getLogger(__name__)

@register.filter('startswith')
def startswith(text, starts):
    LOGGER.debug('startswith entered...')
    if isinstance(text, "".__class__):
        LOGGER.info("Got string: %s", text)
        return text.startswith(starts)
    else:
        LOGGER.info("Got non-string: %s", text)
    return False
