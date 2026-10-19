import base64
import hashlib
from typing import Any

from hook_utils import find_class

from LiteGram.data.dex import DEX_B64, DEX_HASH

_class_loader: Any = None
_loaded_classes: dict[str, Any] = {}


def get_dex_class_loader(plugin: Any = None) -> Any:
    global _class_loader
    if _class_loader is not None:
        return _class_loader

    if not DEX_B64:
        return None

    try:
        ApplicationLoader = find_class("org.telegram.messenger.ApplicationLoader")
        if not ApplicationLoader:
            return None
        context = getattr(ApplicationLoader, "applicationContext", None)
        if not context:
            return None

        dex_bytes = base64.b64decode(DEX_B64)
        if hashlib.sha256(dex_bytes).hexdigest() != DEX_HASH:
            if plugin:
                plugin.log("[LiteGram] Security Error: DEX hash mismatch!")
            return None

        parent_cl = context.getClassLoader()
        ByteBuffer = find_class("java.nio.ByteBuffer")
        if not ByteBuffer:
            return None
        dex_buffer = ByteBuffer.wrap(dex_bytes)
        InMemoryDexClassLoader = find_class("dalvik.system.InMemoryDexClassLoader")
        if InMemoryDexClassLoader:
            try:
                _class_loader = InMemoryDexClassLoader(dex_buffer, parent_cl)
            except Exception:
                pass
        if _class_loader is None:
            DexClassLoader = find_class("dalvik.system.DexClassLoader")
            if not DexClassLoader:
                if plugin:
                    plugin.log("[LiteGram] No DexClassLoader available")
                return None
            cache_dir = context.getCacheDir().getAbsolutePath()
            code_cache = context.getCodeCacheDir().getAbsolutePath()
            dex_path = f"{cache_dir}/litegram.dex"
            with open(dex_path, "wb") as f:
                f.write(dex_bytes)
            _class_loader = DexClassLoader(dex_path, code_cache, None, parent_cl)

        return _class_loader
    except Exception as e:
        if plugin:
            plugin.log(f"[LiteGram] Failed to create DEX ClassLoader: {e}")
        return None


def load_dex_class(class_name: str, plugin: Any = None) -> Any | None:
    if class_name in _loaded_classes:
        return _loaded_classes[class_name]
    cl = get_dex_class_loader(plugin)
    if not cl:
        return None
    try:
        dex_cls = cl.loadClass(class_name)
        if dex_cls:
            _loaded_classes[class_name] = dex_cls
        return dex_cls
    except Exception as e:
        if plugin:
            plugin.log(f"[LiteGram] Failed to load DEX class {class_name}: {e}")
        return None


def unload_all_dex() -> None:
    for _, cls in list(_loaded_classes.items()):
        try:
            cls.getMethod("unload").invoke(None)
        except Exception:
            pass
    _loaded_classes.clear()
