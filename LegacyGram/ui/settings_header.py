__id__ = "legacygram"
__version__ = "1.3.0"


def create_header(context):
    try:
        from android.util import TypedValue  # ty: ignore
        from android.view import Gravity  # ty: ignore
        from android.widget import FrameLayout, TextView  # ty: ignore
        from org.telegram.messenger import AndroidUtilities  # ty: ignore
        from org.telegram.ui.ActionBar import Theme  # ty: ignore
        from org.telegram.ui.Components import LayoutHelper  # ty: ignore

        container = FrameLayout(context)

        try:
            from org.telegram.ui.Components.Premium import StarParticlesView  # ty: ignore

            particles = StarParticlesView(context)
            particles.setClipWithGradient()
            particles.drawable.colorKey = Theme.key_premiumStarGradient2
            particles.drawable.isCircle = True
            particles.drawable.centerOffsetY = AndroidUtilities.dp(0)
            particles.drawable.minLifeTime = 2000
            particles.drawable.randLifeTime = 3000
            particles.drawable.useRotate = False
            particles.drawable.updateColors()
            container.addView(particles, LayoutHelper.createFrame(-1, 220, Gravity.CENTER_HORIZONTAL | Gravity.TOP, 0, 0, 0, 0))
            AndroidUtilities.runOnUIThread(lambda: particles.flingParticles(360), 200)
        except Exception:
            pass

        title = TextView(context)
        title.setTextColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText))
        title.setTypeface(AndroidUtilities.getTypeface(AndroidUtilities.TYPEFACE_ROBOTO_MEDIUM))
        title.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 22)
        title.setText("LegacyGram")
        title.setSingleLine(True)
        title.setGravity(Gravity.CENTER)
        container.addView(title, LayoutHelper.createFrame(-2, -2, Gravity.CENTER | Gravity.TOP, 50, 64, 50, 27))

        return container
    except Exception:
        return None
