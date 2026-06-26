import weakref

from android_utils import run_on_ui_thread
from hook_utils import find_class, get_private_field

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
                from com.exteragram.messenger.plugins.models import HeaderSetting  # ty: ignore
                from org.telegram.ui.Components import UItem  # ty: ignore

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
        from android.util import TypedValue  # ty: ignore
        from android.view import Gravity  # ty: ignore
        from android.widget import FrameLayout, TextView  # ty: ignore
        from org.telegram.messenger import AndroidUtilities, ImageLocation, MediaDataController  # ty: ignore
        from org.telegram.ui.ActionBar import Theme  # ty: ignore
        from org.telegram.ui.Components import BackupImageView, LayoutHelper  # ty: ignore

        container = FrameLayout(context)

        try:
            from org.telegram.ui.Components.Premium import StarParticlesView  # ty: ignore

            particlesView = StarParticlesView(context)
            particlesView.setClipWithGradient()
            particlesView.drawable.colorKey = Theme.key_premiumStarGradient2
            particlesView.drawable.isCircle = True
            particlesView.drawable.centerOffsetY = AndroidUtilities.dp(0)
            particlesView.drawable.minLifeTime = 2000
            particlesView.drawable.randLifeTime = 3000
            particlesView.drawable.useRotate = False
            particlesView.drawable.updateColors()
            container.addView(particlesView, LayoutHelper.createFrame(-1, 220, Gravity.CENTER_HORIZONTAL | Gravity.TOP, 0, 0, 0, 0))
            run_on_ui_thread(lambda: particlesView.flingParticles(360), 200)
        except Exception:
            pass

        imageView = BackupImageView(context)
        imageView.setRoundRadius(0)
        imageView.setClickable(True)

        def try_load_sticker(img):
            try:
                pack_name, sticker_index_str = __icon__.split("/")
                sticker_index = int(sticker_index_str)
                ss = MediaDataController.getInstance(0).getStickerSetByName(pack_name) or MediaDataController.getInstance(0).getStickerSetByEmojiOrName(
                    pack_name
                )
                if ss and ss.documents and ss.documents.size() > 0:
                    sticker_index = min(sticker_index, ss.documents.size() - 1)
                    img.setImage(ImageLocation.getForDocument(ss.documents.get(sticker_index)), "108_108", None, None, 0, 1)
                    return True
            except Exception:
                pass
            return False

        if not try_load_sticker(imageView):
            try:
                pack_name, _ = __icon__.split("/")
                MediaDataController.getInstance(0).loadStickersByEmojiOrName(pack_name, False, False)
                run_on_ui_thread(lambda: try_load_sticker(imageView), 1500)
            except Exception:
                pass

        container.addView(imageView, LayoutHelper.createFrame(108, 108, Gravity.CENTER | Gravity.TOP, 0, 20, 0, 0))

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

        try:
            from android.view import MotionEvent, View  # ty: ignore
            from java import dynamic_proxy  # ty: ignore

            class BounceTouchListener(dynamic_proxy(View.OnTouchListener)):  # ty: ignore
                def onTouch(self, v, event):
                    action = event.getAction()
                    if action == MotionEvent.ACTION_DOWN:
                        v.animate().scaleX(0.9).scaleY(0.9).setDuration(100).start()
                    elif action == MotionEvent.ACTION_UP or action == MotionEvent.ACTION_CANCEL:
                        v.animate().scaleX(1.0).scaleY(1.0).setDuration(100).start()
                    return False

            imageView.setOnTouchListener(BounceTouchListener())
        except Exception:
            pass

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
