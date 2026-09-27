# type: ignore
import weakref

from hook_utils import find_class, get_private_field
from java import jint

from LiteGram.header import __icon__, __name__
from LiteGram.i18n.i18n import t
from LiteGram.utils.xposed_utils import BaseHook


class LiteGramSettingsHeaderHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin)
        self._plugin_ref = weakref.ref(plugin)

    def after_hooked_method(self, param):
        try:
            plugin = self._plugin_ref()
            if not plugin:
                return

            activity = param.thisObject
            items = param.args[0]
            if not items or items.size() == 0:
                return

            plugin_obj = get_private_field(activity, "plugin")
            if not plugin_obj or str(plugin_obj.getId()) != "litegram":
                return

            if get_private_field(activity, "createSubFragmentCallback") is not None:
                return

            searching = get_private_field(activity, "searching")
            if searching:
                return

            header = _create_litegram_settings_header(activity.getContext())
            if header:
                from com.exteragram.messenger.plugins.models import HeaderSetting
                from org.telegram.ui.Components import UItem

                item = UItem.asCustom(header)
                item.settingItem = HeaderSetting("litegram_header")
                try:
                    item.setTransparent(True)
                except Exception:
                    pass
                items.add(0, item)
                items.add(1, UItem.asShadow())
        except Exception:
            pass


def _create_litegram_settings_header(context):
    try:
        FrameLayout = find_class("android.widget.FrameLayout")
        container = FrameLayout(context)

        Theme = find_class("org.telegram.ui.ActionBar.Theme")
        AndroidUtilities = find_class("org.telegram.messenger.AndroidUtilities")
        LayoutHelper = find_class("org.telegram.ui.Components.LayoutHelper")
        Gravity = find_class("android.view.Gravity")

        BackupImageView = find_class("org.telegram.ui.Components.BackupImageView")
        imageView = BackupImageView(context)
        imageView.setRoundRadius(AndroidUtilities.dp(16))

        try:
            receiver = imageView.getImageReceiver()
            if receiver:
                receiver.setAutoRepeat(1)
        except Exception:
            pass

        if __icon__ and "/" in __icon__:
            try:
                pack_name, sticker_index_str = __icon__.rsplit("/", 1)
                sticker_index = int(sticker_index_str.strip())

                MediaDataController = find_class("org.telegram.messenger.MediaDataController")
                UserConfig = find_class("org.telegram.messenger.UserConfig")
                account = int(getattr(UserConfig, "selectedAccount", 0))

                loaded = False
                if MediaDataController:
                    mdc = MediaDataController.getInstance(account)
                    if mdc:
                        try:
                            mdc.setPlaceholderImageByIndex(imageView, pack_name, jint(sticker_index), "108_108")
                            loaded = True
                        except Exception:
                            try:
                                mdc.setPlaceholderImageByIndex(imageView, pack_name, sticker_index, "108_108")
                                loaded = True
                            except Exception:
                                pass

                        if not loaded:
                            try:
                                ss = mdc.getStickerSetByName(pack_name) or mdc.getStickerSetByEmojiOrName(pack_name)
                                if ss and ss.documents and ss.documents.size() > 0:
                                    idx = min(sticker_index, ss.documents.size() - 1)
                                    doc = ss.documents.get(idx)
                                    if doc:
                                        ImageLocation = find_class("org.telegram.messenger.ImageLocation")
                                        DocumentObject = find_class("org.telegram.messenger.DocumentObject")
                                        thumb = DocumentObject.getSvgThumb(doc, Theme.key_windowBackgroundWhiteGrayIcon, 0.2) if DocumentObject else None
                                        if ImageLocation:
                                            imageView.setImage(
                                                ImageLocation.getForDocument(doc),
                                                "108_108",
                                                thumb,
                                                0,
                                                doc,
                                            )
                            except Exception:
                                pass
            except Exception:
                pass

        container.addView(imageView, LayoutHelper.createFrame(108, 108, Gravity.CENTER | Gravity.TOP, 0, 20, 0, 0))

        TextView = find_class("android.widget.TextView")
        TypedValue = find_class("android.util.TypedValue")

        title = TextView(context)
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText))
        title.setTypeface(AndroidUtilities.getTypeface(AndroidUtilities.TYPEFACE_ROBOTO_MEDIUM))
        title.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 22)
        title.setText(__name__)
        title.setSingleLine(True)
        title.setGravity(Gravity.CENTER)
        container.addView(title, LayoutHelper.createFrame(-2, -2, Gravity.CENTER | Gravity.TOP, 50, 145, 50, 0))

        subtitle = TextView(context)
        subtitle.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteGrayText))
        subtitle.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 14)
        subtitle.setText(t("plugin_description"))
        subtitle.setGravity(Gravity.CENTER)
        container.addView(subtitle, LayoutHelper.createFrame(-2, -2, Gravity.CENTER | Gravity.TOP, 60, 180, 60, 27))

        return container
    except Exception:
        return None


def register_settings_header(plugin):
    PSA = find_class("com.exteragram.messenger.plugins.ui.PluginSettingsActivity")
    if PSA:
        try:
            method = PSA.getClass().getDeclaredMethod("fillItems", find_class("java.util.ArrayList"), find_class("org.telegram.ui.Components.UniversalAdapter"))
            method.setAccessible(True)
            plugin.hook_method(method, LiteGramSettingsHeaderHook(plugin))
        except Exception:
            pass
