package non.feature.litegram.core

object LiteGramBridge {
    @Volatile @JvmStatic private var core: LiteGramCore? = null

    @JvmStatic
    @Synchronized
    fun load(cl: ClassLoader) {
        try {
            core?.unload()
        } catch (_: Throwable) {}
        core = null
        val newCore = LiteGramCore()
        try {
            newCore.load(cl)
            core = newCore
        } catch (t: Throwable) {
            try {
                newCore.unload()
            } catch (_: Throwable) {}
            core = null
            throw t
        }
    }

    @JvmStatic
    @Synchronized
    fun unload() {
        val current = core ?: return
        try {
            current.unload()
        } finally {
            core = null
        }
    }

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        core?.setFlag(name, enabled)
    }

    @JvmStatic
    fun isLoaded(): Boolean = core != null
}
