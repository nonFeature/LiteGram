import base64
import hashlib
import traceback
import zlib
from typing import Any

from hook_utils import find_class

from LiteGram.data.dex import DEX_B64, DEX_HASH

ENTRY_CLASS = "non.feature.litegram.core.LiteGramBridge"


class NativeBridge:
    def __init__(self, entry_class: str = ENTRY_CLASS):
        self.entry_class = entry_class
        self.clazz: Any = None
        self.loader: Any = None
        self.loaded: bool = False
        self._method_cache: dict[tuple[str, int], Any] = {}

    def load(self, plugin: Any = None, force: bool = False) -> None:
        if self.loaded:
            if not force:
                return
            self.unload()
        if not DEX_B64:
            return

        try:
            ApplicationLoader = find_class("org.telegram.messenger.ApplicationLoader")
            if not ApplicationLoader:
                return
            context = getattr(ApplicationLoader, "applicationContext", None)
            parent_loader = None
            if context:
                try:
                    parent_loader = context.getClassLoader()
                except Exception:
                    parent_loader = None
            if parent_loader is None and hasattr(ApplicationLoader, "getClass"):
                try:
                    parent_loader = ApplicationLoader.getClass().getClassLoader()
                except Exception:
                    parent_loader = None
            if not parent_loader:
                return

            raw_payload = base64.b64decode(DEX_B64)
            try:
                dex_bytes = zlib.decompress(raw_payload)
            except Exception:
                dex_bytes = raw_payload

            if hashlib.sha256(dex_bytes).hexdigest() != DEX_HASH:
                if plugin:
                    plugin.log("[LiteGram] Security Error: DEX hash mismatch!")
                return

            ByteBuffer = find_class("java.nio.ByteBuffer")
            InMemoryDexClassLoader = find_class("dalvik.system.InMemoryDexClassLoader")
            if InMemoryDexClassLoader and ByteBuffer:
                try:
                    self.loader = InMemoryDexClassLoader(ByteBuffer.wrap(dex_bytes), parent_loader)
                    self.clazz = self.loader.loadClass(self.entry_class)
                except Exception:
                    self.clazz = None
                    self.loader = None

            if self.clazz is None and context:
                cache_dir = context.getCacheDir().getAbsolutePath()
                code_cache = context.getCodeCacheDir().getAbsolutePath()
                dex_path = f"{cache_dir}/litegram_{DEX_HASH[:12]}.dex"
                with open(dex_path, "wb") as f:
                    f.write(dex_bytes)
                DexClassLoader = find_class("dalvik.system.DexClassLoader")
                if DexClassLoader:
                    self.loader = DexClassLoader(dex_path, code_cache, None, parent_loader)
                    self.clazz = self.loader.loadClass(self.entry_class)

            if self.clazz is None:
                return

            self._invoke("load", parent_loader)
            self.loaded = True
            if plugin:
                plugin.log("[LiteGram] Core DEX bridge loaded successfully.")
        except Exception as e:
            try:
                self._invoke("unload")
            except Exception:
                pass
            self.loaded = False
            self.clazz = None
            self.loader = None
            self._method_cache.clear()
            if plugin:
                plugin.log(f"[LiteGram] Failed to load Core DEX bridge: {e}\n{traceback.format_exc()}")

    def unload(self) -> None:
        if self.clazz is not None and self.loaded:
            try:
                self._invoke("unload")
            except Exception:
                pass
        self.loaded = False
        self.clazz = None
        self.loader = None
        self._method_cache.clear()

    def set_flag(self, name: str, enabled: bool) -> None:
        if self.clazz is None or not self.loaded:
            return
        try:
            self._invoke("setFlag", str(name), bool(enabled))
        except Exception as e:
            try:
                XposedBridge = find_class("de.robv.android.xposed.XposedBridge")
                if XposedBridge:
                    XposedBridge.log(f"LiteGram [dex_bridge] set_flag({name}, {enabled}) error: {e}")
            except Exception:
                pass

    def is_loaded(self) -> bool:
        return self.loaded and self.clazz is not None

    def _invoke(self, method_name: str, *args: Any) -> Any:
        if self.clazz is None:
            raise RuntimeError("DEX class is not loaded")
        cache_key = (method_name, len(args))
        cached = self._method_cache.get(cache_key)
        if not cached:
            for method in self.clazz.getDeclaredMethods():
                if str(method.getName()) == method_name and len(method.getParameterTypes()) == len(args):
                    method.setAccessible(True)
                    param_type_names = [str(pt.getName()) for pt in method.getParameterTypes()]
                    cached = (method, param_type_names)
                    self._method_cache[cache_key] = cached
                    break
            if not cached:
                raise RuntimeError(f"method not found: {method_name}/{len(args)}")

        method, param_type_names = cached
        converted_args = []
        BooleanClass = find_class("java.lang.Boolean")
        IntegerClass = find_class("java.lang.Integer")
        LongClass = find_class("java.lang.Long")

        for i, arg in enumerate(args):
            pt = param_type_names[i]
            if pt in ("boolean", "java.lang.Boolean") and BooleanClass:
                converted_args.append(BooleanClass.valueOf(bool(arg)))
            elif pt in ("int", "java.lang.Integer") and IntegerClass:
                converted_args.append(IntegerClass.valueOf(int(arg)))
            elif pt in ("long", "java.lang.Long") and LongClass:
                converted_args.append(LongClass.valueOf(int(arg)))
            elif pt in ("java.lang.String", "str"):
                converted_args.append(str(arg))
            else:
                converted_args.append(arg)

        target = None
        try:
            target = self.clazz.getField("INSTANCE").get(None)
        except Exception:
            pass
        return method.invoke(target, *converted_args)


dex_bridge = NativeBridge(ENTRY_CLASS)


def get_dex_class_loader(plugin: Any = None) -> Any:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    return dex_bridge.loader


def load_dex_class(class_name: str, plugin: Any = None) -> Any | None:
    loader = get_dex_class_loader(plugin)
    if not loader:
        return None
    try:
        return loader.loadClass(class_name)
    except Exception:
        return None


def unload_all_dex() -> None:
    dex_bridge.unload()
