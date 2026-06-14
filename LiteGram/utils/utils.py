from client_utils import get_last_fragment
from hook_utils import find_class
from java.lang import Runtime
from ui.bulletin import BulletinHelper

_cached_version = None


def get_client_version() -> str:
    global _cached_version
    if _cached_version is not None:
        return _cached_version
    try:
        BuildVars = find_class("org.telegram.messenger.BuildVars")
        if BuildVars:
            _cached_version = str(BuildVars.BUILD_VERSION_STRING)
            return _cached_version
    except Exception:
        pass
    _cached_version = "Unknown"
    return _cached_version


def parse_version(version: str):
    try:
        return tuple(map(int, version.split(".")))
    except ValueError:
        return 0, 0, 0


def open_url(url: str) -> None:
    try:
        current_fragment = get_last_fragment()
        if not current_fragment:
            return

        context = current_fragment.getParentActivity()
        if not context:
            return

        Browser = find_class("org.telegram.messenger.browser.Browser")
        if Browser:
            # or we can use openUrlInSystemBrowser,
            Browser.openUrl(context, url)
    except Exception as e:
        BulletinHelper.show_error(f"Failed to open url {url}: {e}")


# Thx extera
def restart_app() -> None:
    current_fragment = get_last_fragment()
    if not current_fragment:
        return
    context = current_fragment.getParentActivity()
    if context:
        package_name = context.getPackageName()
        pm = context.getPackageManager()
        launch_intent = pm.getLaunchIntentForPackage(package_name)

        Intent = find_class("android.content.Intent")
        restart_intent = Intent.makeRestartActivityTask(launch_intent.getComponent())  # ty: ignore
        restart_intent.setPackage(package_name)
        context.startActivity(restart_intent)

        Runtime.getRuntime().exit(0)
