import logging
from pymacaron.config import get_config
from pymacaron.utils import get_app_name


log = logging.getLogger(__name__)


# Which monitoring methods to use
use_scout = False


def monitor_init(app=None, config=None, celery=False):

    log.debug("Init monitoring with app=%s config=%s celery=%s" % (app, config, celery))

    if not config:
        config = get_config()

    global use_scout

    # Note: at this point, pym_monitor should have been called earlier on to
    # start any eventual agent daemon required by the monitoring app.

    # Enable scoutapp monitoring
    if hasattr(config, 'scout_key'):
        use_scout = True
        appname = get_app_name()
        scout_key = config.scout_key

        if celery:
            log.info("Setting up scoutapp monitoring for Celery jobs")
            import scout_apm.celery
            from scout_apm.api import Config

            Config.set(
                key=scout_key,
                name=appname,
                monitor=True,
            )

            scout_apm.celery.install()

        elif app:

            # Enable Flask monitoring for scoutapp
            log.info("Setting up scoutapp monitoring for Flask app")
            from scout_apm.flask import ScoutApm
            ScoutApm(app)
            app.config['SCOUT_KEY'] = scout_key
            app.config['SCOUT_NAME'] = appname
            app.config['SCOUT_MONITOR'] = True

    # END OF scoutapp support


class monitor():

    def __init__(self, kind='Unknown', method='Unknown'):
        self.kind = kind
        self.method = method

    def __enter__(self):
        global use_scout
        if use_scout:
            log.debug("START MONITOR %s/%s" % (self.kind, self.method))
            import scout_apm.api
            self.scout_decorator = scout_apm.api.instrument(self.method, tags={}, kind=self.kind)
            self.scout_decorator.__enter__()

    def __exit__(self, type, value, traceback):
        global use_scout
        if use_scout:
            log.debug("STOP MONITOR %s/%s" % (self.kind, self.method))
            self.scout_decorator.__exit__(type, value, traceback)
