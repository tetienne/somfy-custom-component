"""Define constants for the Somfy component."""

from homeassistant.const import SERVICE_SET_COVER_POSITION

DOMAIN = "somfy"
COORDINATOR = "coordinator"
API = "api"
CONF_OPTIMISTIC = "optimistic"

SERVICE_OPEN_COVER_SLOWLY = "open_cover_slowly"
SERVICE_CLOSE_COVER_SLOWLY = "close_cover_slowly"
SERVICE_SET_COVER_POSITION_SLOWLY = "set_cover_position_slowly"
