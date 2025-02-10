from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components.calendar import CalendarEntity
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class CalendarEventData:
    summary: str
    start: dict
    end: dict
    description: str = ""
    location: str = ""


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    coordinator = hass.data[DOMAIN]["coordinator"]
    _LOGGER.debug("Initialisiere Kalender-Entität für FHV A5 Stundenplan")
    async_add_entities([A5StundenplanCalendar(coordinator)], True)


class A5StundenplanCalendar(CalendarEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "FHV A5 Stundenplan"
        _LOGGER.debug("Kalender-Entität '%s' initialisiert", self._attr_name)

    @property
    def device_state_attributes(self):
        attrs = {"last_update": self.coordinator.last_update_success}
        _LOGGER.debug("Geräteattribute: %s", attrs)
        return attrs

    @property
    def event(self):
        return None

    async def async_get_events(self, hass: HomeAssistant, start, end):
        events = []
        if not self.coordinator.data:
            _LOGGER.warning("Keine Daten im Koordinator vorhanden")
            return events

        _LOGGER.debug("Erstelle Events aus Daten im Zeitraum %s bis %s", start, end)
        for event in self.coordinator.data.get("data", []):
            try:
                event_start = datetime.strptime(
                    event["start_date"], "%Y-%m-%d %H:%M:%S"
                )
                event_end = datetime.strptime(event["end_date"], "%Y-%m-%d %H:%M:%S")
            except ValueError as err:
                _LOGGER.error(
                    "Fehler beim Parsen des Datums für Event %s: %s", event, err
                )
                continue

            _LOGGER.debug(
                "Event '%s' hinzugefügt: Start %s, Ende %s",
                event.get("event_name", "Kein Titel"),
                event_start,
                event_end,
            )

            if event.get("occasion") == "Prüfung":
                event_summary = f"Prüfung: {event.get('event_subject', 'Kein Titel')}, Raum: {event.get('rooms', '-')}"
            else:
                event_summary = f"{event.get('event_subject', 'Kein Titel')}, Raum: {event.get('rooms', '-')}"

            event_description = f"Lecturers: {event.get('lecturers', '-')}   Gruppen: {event.get('planning_groups', '-')}   Räume: {event.get('rooms', '-')}"

            events.append(
                CalendarEventData(
                    summary=event_summary,
                    start={"dateTime": dt_util.as_local(event_start).isoformat()},
                    end={"dateTime": dt_util.as_local(event_end).isoformat()},
                    description=event_description,
                    location=event.get("rooms", "Kein Raum"),
                )
            )
        _LOGGER.debug("Erstellte %d Events", len(events))
        return events
