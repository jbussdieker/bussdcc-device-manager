import click

from bussdcc_framework import Runtime, ReplayRuntime
from bussdcc_framework.io import ConsoleSink, JsonlSink, JsonlSource
from bussdcc_system import process as system_process, service as system_service

from . import process, service, interface

from .version import __version__

PLUGINS = [
    "bootstrap",
    "bootstrap-layout",
    "socketio",
    "formtree",
]


def history_path(data_dir: str) -> str:
    return f"{data_dir}/history"


@click.group()
def main() -> None:
    """Device Manager"""


@main.command()
@click.option("--record", is_flag=True, default=False)
@click.option("--record-interval", default=600.0)
@click.option("--data-dir", default="data")
@click.option("--quiet", is_flag=True, default=False)
@click.option("--web", is_flag=True, default=False)
@click.option("--web-host", default="127.0.0.1")
@click.option("--web-port", default=8000)
def run(
    record: bool,
    record_interval: float,
    data_dir: str,
    quiet: bool,
    web: bool,
    web_host: str,
    web_port: int,
) -> None:
    runtime = Runtime()
    runtime.ctx.state.set("app.version", __version__)

    if not quiet:
        runtime.add_sink(ConsoleSink())

    if record:
        runtime.add_sink(
            JsonlSink(root=history_path(data_dir), interval=record_interval)
        )

    runtime.processes.register(system_process.SystemIdentityProcess())
    runtime.processes.register(process.ConfigProcess())

    runtime.services.register(system_service.SystemIdentityService())
    runtime.services.register(service.ConfigService(data_dir))
    runtime.services.register(service.DeviceManagerService())

    if web:
        runtime.interfaces.register(
            interface.WebInterface(
                __name__,
                host=web_host,
                port=web_port,
                template_folder="interface/web/templates",
                plugins=PLUGINS,
            )
        )

    runtime.run()


@main.command()
@click.option("--speed", "-s", default=5.0)
@click.option("--data-dir", "-d", default="data")
@click.option("--web", is_flag=True, default=False)
@click.option("--web-host", default="127.0.0.1")
@click.option("--web-port", default=8000)
def replay(
    speed: float, data_dir: str, web: bool, web_host: str, web_port: int
) -> None:
    source = JsonlSource(root=history_path(data_dir))

    runtime = ReplayRuntime(speed=speed)
    runtime.ctx.state.set("app.version", __version__)

    runtime.add_sink(ConsoleSink())

    runtime.processes.register(system_process.SystemIdentityProcess())
    runtime.processes.register(process.ConfigProcess())

    if web:
        runtime.interfaces.register(
            interface.WebInterface(
                __name__,
                host=web_host,
                port=web_port,
                template_folder="interface/web/templates",
                plugins=PLUGINS,
            )
        )

    runtime.replay(source)
