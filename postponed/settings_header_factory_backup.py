import traceback

from hook_utils import find_class
from java import jfloat
from ui.settings import SimpleSettingFactory  # type: ignore

from LiteGram.header import __name__
from LiteGram.i18n.i18n import t


def to_signed_int(val):
    val = int(val) & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val


_cached_path = None


def _create_litegram_settings_header(context):
    try:
        HeaderSettingsCell = find_class("com.exteragram.messenger.preferences.components.HeaderSettingsCell")
        if not HeaderSettingsCell:
            return None
        header = HeaderSettingsCell(context)

        # Set plugin title and description
        header.titleTextView.setText(__name__)
        header.subtitleTextView.setText(t("plugin_description"))

        # Reset bold style and reduce font size for the description
        try:
            header.subtitleTextView.setTypeface(None)
            header.subtitleTextView.setTextSize(14.0)
        except Exception:
            pass

        PATH_DATA = (
            "M 19.325 87.4917 V 63.6333 C 19.325 58.9185 20.9866 54.8995 24.3097 51.5764 "
            "C 27.6328 48.2532 31.6518 46.5917 36.3667 46.5917 H 39.775 V 19.325 "
            "C 39.775 17.4504 40.4425 15.8457 41.7774 14.5107 C 43.1123 13.1758 44.7171 12.5083 46.5917 12.5083 H 53.4083 "
            "C 55.2829 12.5083 56.8877 13.1758 58.2226 14.5107 C 59.5575 15.8457 60.225 19.325 60.225 19.325 V 46.5917 H 63.6333 "
            "C 68.3482 46.5917 72.3672 48.2532 75.6903 51.5764 C 79.0134 54.8995 80.675 58.9185 80.675 63.6333 V 87.4917 H 19.325 Z "
            "M 26.1417 80.675 H 32.9583 V 70.45 C 32.9583 69.4843 33.285 68.6748 33.9382 68.0216 "
            "C 34.5915 67.3683 35.401 67.0417 36.3667 67.0417 C 37.3324 67.0417 38.1418 67.3683 38.7951 68.0216 "
            "C 39.4484 68.6748 39.775 69.4843 39.775 70.45 V 80.675 H 46.5917 V 70.45 "
            "C 46.5917 69.4843 46.9183 68.6748 47.5716 68.0216 C 48.2248 67.3683 49.0343 67.0417 50.0 67.0417 "
            "C 50.9657 67.0417 51.7752 67.3683 52.4284 68.0216 C 53.0817 68.6748 53.4083 69.4843 53.4083 70.45 V 80.675 H 60.225 V 70.45 "
            "C 60.225 69.4843 60.5516 68.6748 61.2049 68.0216 C 61.8582 67.3683 62.6676 67.0417 63.6333 67.0417 "
            "C 64.599 67.0417 65.4085 67.3683 66.0618 68.0216 C 66.715 68.6748 67.0417 69.4843 67.0417 70.45 V 80.675 H 73.8583 V 63.6333 "
            "C 73.8583 60.7931 72.8642 58.3788 70.876 56.3906 C 68.8878 54.4024 66.4736 53.4083 63.6333 53.4083 H 36.3667 "
            "C 33.5264 53.4083 31.1122 54.4024 29.124 56.3906 C 27.1358 58.3788 26.1417 60.7931 26.1417 63.6333 V 80.675 Z "
            "M 53.4083 46.5917 V 19.325 H 46.5917 V 46.5917 H 53.4083 Z"
        )

        try:
            from org.telegram.ui.ActionBar import Theme  # ty: ignore

            active_theme = Theme.getActiveTheme()

            # Determine theme type and calculate colors
            is_monet = False
            try:
                if active_theme and active_theme.isMonet() and find_class("android.os.Build").VERSION.SDK_INT >= 31:  # type: ignore
                    is_monet = True
            except Exception:
                pass

            if is_monet:
                MonetUtils = find_class("com.exteragram.messenger.utils.ui.MonetUtils")
                bg_color = MonetUtils.getColor("a2_800" if active_theme.isDark() else "a1_100")  # type: ignore
                brush_color = MonetUtils.getColor("a1_200" if active_theme.isDark() else "a1_700")  # type: ignore
            else:
                # Use default LiteGram colors for non-monet theme (yellow background, black brush)
                bg_color = 0xFFEEC643
                brush_color = 0xFF000000

            # Parse path once per app lifetime
            global _cached_path
            if _cached_path is None:
                PathParser = find_class("androidx.core.graphics.PathParser")
                path = PathParser.createPathFromPathData(PATH_DATA)  # type: ignore

                # Scale path 2x to fit 200x200 bitmap
                Matrix = find_class("android.graphics.Matrix")
                matrix = Matrix()  # type: ignore
                matrix.setScale(jfloat(2.0), jfloat(2.0))
                path.transform(matrix)
                _cached_path = path

            # Render Path to a static Bitmap for smooth GPU rendering
            Bitmap = find_class("android.graphics.Bitmap")
            # Create a 200x200 bitmap (sufficient for high-res 72dp icon)
            bitmap = Bitmap.createBitmap(200, 200, Bitmap.Config.ARGB_8888)  # type: ignore

            Canvas = find_class("android.graphics.Canvas")
            canvas = Canvas(bitmap)  # type: ignore

            Paint = find_class("android.graphics.Paint")
            paint = Paint()  # type: ignore
            paint.setAntiAlias(True)
            paint.setStyle(Paint.Style.FILL)  # type: ignore

            Integer = find_class("java.lang.Integer")
            java_brush_color = Integer(to_signed_int(brush_color))  # type: ignore

            # Set brush color
            try:
                paint.getClass().getMethod("setColor", [Integer.TYPE]).invoke(paint, [java_brush_color])  # type: ignore
            except Exception:
                paint.setColor(java_brush_color)

            # Draw path on the bitmap
            canvas.drawPath(_cached_path, paint)

            # Create BitmapDrawable
            BitmapDrawable = find_class("android.graphics.drawable.BitmapDrawable")
            logo_drawable = BitmapDrawable(context.getResources(), bitmap)  # type: ignore

            header.imageView.setBackgroundColor(to_signed_int(bg_color))
            header.imageView.setImageDrawable(logo_drawable)
        except Exception:
            traceback.print_exc()

        return header
    except Exception:
        traceback.print_exc()
        return None


def _create_header_view(context, list_view, current_account: int, class_guid: int, resources_provider):
    return _create_litegram_settings_header(context)


def _bind_header_view(view, item, divider: bool, adapter, list_view):
    pass


HeaderSettingsFactory = SimpleSettingFactory(
    _create_header_view,
    _bind_header_view,
    is_clickable=False,
    is_shadow=False,
)
