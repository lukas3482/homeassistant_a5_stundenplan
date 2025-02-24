import logging
from datetime import datetime, timedelta
from functools import partial

import async_timeout
from dateutil.relativedelta import relativedelta
import voluptuous as vol

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config):
    """Set up the FHV A5 Stundenplan integration."""

    conf = config.get(DOMAIN)
    if conf is None:
        _LOGGER.error("Keine Konfiguration für %s gefunden", DOMAIN)
        return False

    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    _LOGGER.info("Setze FHV A5 Stundenplan Integration mit Benutzer %s", username)

    # Create the coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="FHV A5 Stundenplan",
        # We use partial to pass hass, username and password into our async update function
        update_method=partial(async_update_data, hass, username, password),
        update_interval=timedelta(hours=1),
    )

    # Do an immediate refresh
    await coordinator.async_refresh()

    # Store the coordinator in hass.data so other platforms (calendar) can access it
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = coordinator

    _LOGGER.info("Initialer Datenabruf abgeschlossen. Kalender-Plattform wird geladen")
    # This loads the calendar platform, passing our domain and config
    load_platform(hass, "calendar", DOMAIN, {}, config)

    return True


async def async_update_data(hass: HomeAssistant, username: str, password: str):
    """
    Perform the actual data-fetching logic:
    1) Login to the target site
    2) Get the schedule
    3) Return the parsed JSON data
    """

    login_url = "https://a5.fhv.at/ajax/120/LoginResponsive/LoginHandler"
    schedule_url_base = "https://a5.fhv.at/ajax/122/EventPlanerSite/EventDateSiteJsonPage"
    login_data = {
        "password": password,
        "username": username,
        "domain-id": 8,
        "permanent-login": 0,
    }

    # Get the async aiohttp session from Home Assistant
    session = async_get_clientsession(hass)

    # Try logging in
    try:
        async with async_timeout.timeout(10):
            _LOGGER.debug("Sende Login-Daten an %s", login_url)
            async with session.post(login_url, data=login_data) as login_response:
                if login_response.status != 200:
                    raise UpdateFailed(
                        f"Login fehlgeschlagen: Status {login_response.status}"
                    )
                # If the site sets cookies, aiohttp's session cookie_jar will store them automatically
                _LOGGER.debug("Login erfolgreich, Cookies gespeichert.")
    except Exception as err:
        raise UpdateFailed(f"Fehler beim Login: {err}") from err

    # Calculate the date range for the schedule
    now = datetime.now().date()
    start_date = now - relativedelta(months=6)
    end_date = now + relativedelta(months=6)
    _LOGGER.debug(
        "Berechneter Zeitraum: Start %s, Ende %s",
        start_date.isoformat(),
        end_date.isoformat(),
    )

    schedule_url = (
        f"{schedule_url_base}?from={start_date.isoformat()}&to={end_date.isoformat()}"
    )

    # Fetch the schedule data
    try:
        async with async_timeout.timeout(10):
            _LOGGER.debug("Abrufen des Stundenplans von %s", schedule_url)
            async with session.get(schedule_url) as schedule_response:
                if schedule_response.status != 200:
                    raise UpdateFailed(
                        f"Stundenplan-Abruf fehlgeschlagen: Status {schedule_response.status}"
                    )

                data = await schedule_response.json()
                _LOGGER.warning("Stundenplan abgerufen")
                if not data or "data" not in data:
                    _LOGGER.error("Keine gültigen Daten im Stundenplan-Abruf erhalten")
                    return None

                return data

    except Exception as err:
        raise UpdateFailed(f"Fehler beim Abruf des Stundenplans: {err}") from err
