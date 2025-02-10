from datetime import datetime, timedelta
import logging

import async_timeout
from dateutil.relativedelta import relativedelta
import voluptuous as vol

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
    conf = config.get(DOMAIN)
    if conf is None:
        _LOGGER.error("Keine Konfiguration für %s gefunden", DOMAIN)
        return False

    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    _LOGGER.info("Setze FHV A5 Stundenplan Integration mit Benutzer %s", username)

    session = async_get_clientsession(hass)

    async def async_update_data():
        login_url = "https://a5.fhv.at/ajax/120/LoginResponsive/LoginHandler"
        login_data = {
            "password": password,
            "username": username,
            "domain-id": 8,
            "permanent-login": 0,
        }
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Sende Login-Daten an %s", login_url)

                login_response = await session.post(login_url, data=login_data)
                if login_response.status != 200:
                    _LOGGER.error(
                        "Login fehlgeschlagen: Status %s", login_response.status
                    )
                    return None

                cookies = login_response.cookies
                _LOGGER.debug("Login erfolgreich, erhaltene Cookies: %s", cookies)
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Login: {err}") from err

        now = datetime.now().date()
        start_date = now - relativedelta(months=6)
        end_date = now + relativedelta(months=6)
        _LOGGER.debug(
            "Berechneter Zeitraum: Start %s, Ende %s",
            start_date.isoformat(),
            end_date.isoformat(),
        )

        schedule_url = (
            f"https://a5.fhv.at/ajax/122/EventPlanerSite/EventDateSiteJsonPage?"
            f"from={start_date.isoformat()}&to={end_date.isoformat()}"
        )
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Abrufen des Stundenplans von %s", schedule_url)
                schedule_response = await session.get(schedule_url, cookies=cookies)
                if schedule_response.status != 200:
                    _LOGGER.error(
                        "Stundenplan-Abruf fehlgeschlagen: Status %s",
                        schedule_response.status,
                    )
                    return None

                data = await schedule_response.json()
                _LOGGER.debug("Abgerufene Stundenplan-Daten: %s", data)
                if not data or "data" not in data:
                    _LOGGER.error("Keine gültigen Daten im Stundenplan-Abruf erhalten")

                return data
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abruf des Stundenplans: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="FHV A5 Stundenplan",
        update_method=async_update_data,
        update_interval=timedelta(hours=1),
    )

    await coordinator.async_refresh()
    hass.data.setdefault(DOMAIN, {})["coordinator"] = coordinator

    _LOGGER.info("Initialer Datenabruf abgeschlossen. Kalender-Plattform wird geladen")
    load_platform(hass, "calendar", DOMAIN, {}, config)
    return True
