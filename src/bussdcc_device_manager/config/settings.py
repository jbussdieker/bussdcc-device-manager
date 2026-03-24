from dataclasses import dataclass, field, replace
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class ScheduleConfig:
    start_datetime: datetime = field(
        metadata={
            "label": "Start Datetime",
            "group": "Schedule",
            "required": True,
            "help": "Datetime used to calculate age and active schedule step.",
        }
    )


@dataclass(frozen=True, slots=True)
class Settings:
    name: str = field(
        metadata={
            "label": "Name",
            "group": "General",
            "required": True,
            "help": "Unique thermostat instance name.",
        }
    )
    schedule: ScheduleConfig = field(
        metadata={
            "label": "Schedule",
            "group": "Control",
            "required": True,
        }
    )
    timezone: str = field(
        default="America/Chicago",
        metadata={
            "label": "Timezone",
            "group": "General",
            "required": True,
            "help": "IANA timezone name used to normalize input.",
        },
    )

    def normalized(self) -> "Settings":
        tz = ZoneInfo(self.timezone)
        start = self.schedule.start_datetime

        if start.tzinfo is None or start.tzinfo.utcoffset(start) is None:
            start = start.replace(tzinfo=tz)
        else:
            start = start.astimezone(tz)

        return replace(
            self,
            schedule=replace(self.schedule, start_datetime=start),
        )


def default_schedule(start_datetime: datetime) -> ScheduleConfig:
    return ScheduleConfig(
        start_datetime=start_datetime,
    )


def build_default_settings(
    start_datetime: datetime | None = None,
    timezone: str = "America/Chicago",
) -> Settings:
    tz = ZoneInfo(timezone)

    if start_datetime is None:
        start_datetime = datetime.now(tz)
    elif (
        start_datetime.tzinfo is None
        or start_datetime.tzinfo.utcoffset(start_datetime) is None
    ):
        start_datetime = start_datetime.replace(tzinfo=tz)
    else:
        start_datetime = start_datetime.astimezone(tz)

    return Settings(
        name="device-manager-1",
        schedule=default_schedule(start_datetime),
        timezone=timezone,
    ).normalized()
