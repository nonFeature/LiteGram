package non.feature.litegram.core

import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.HashMap

object ReflectionCache {
    private val fieldCache = HashMap<String, Field?>()
    private val methodCache = HashMap<String, Method?>()
    private val classCache = HashMap<String, Class<*>?>()
    private val lock = Any()

    fun findClass(name: String, cl: ClassLoader): Class<*>? {
        synchronized(lock) {
            if (classCache.containsKey(name)) {
                return classCache[name]
            }
        }
        val loaded = try {
            Class.forName(name, false, cl)
        } catch (_: Throwable) {
            null
        }
        synchronized(lock) {
            classCache[name] = loaded
        }
        return loaded
    }

    fun getField(clazz: Class<*>?, fieldName: String): Field? {
        if (clazz == null) return null
        val key = clazz.name + "#" + fieldName
        synchronized(lock) {
            if (fieldCache.containsKey(key)) {
                return fieldCache[key]
            }
        }

        var curr: Class<*>? = clazz
        while (curr != null) {
            try {
                val f = curr.getDeclaredField(fieldName)
                f.isAccessible = true
                synchronized(lock) {
                    fieldCache[key] = f
                }
                return f
            } catch (_: NoSuchFieldException) {
                curr = curr.superclass
            }
        }
        synchronized(lock) {
            fieldCache[key] = null
        }
        return null
    }

    fun getFieldValue(obj: Any?, fieldName: String): Any? {
        if (obj == null) return null
        val f = getField(obj.javaClass, fieldName) ?: return null
        return try {
            f.get(obj)
        } catch (_: Throwable) {
            null
        }
    }

    fun setFieldValue(obj: Any?, fieldName: String, value: Any?) {
        if (obj == null) return
        val f = getField(obj.javaClass, fieldName) ?: return
        try {
            f.set(obj, value)
        } catch (_: Throwable) {}
    }

    fun getMethod(clazz: Class<*>?, methodName: String, vararg paramTypes: Class<*>?): Method? {
        if (clazz == null) return null
        val nonNullParams = arrayOfNulls<Class<*>>(paramTypes.size)
        for (i in paramTypes.indices) {
            val p = paramTypes[i] ?: return null
            nonNullParams[i] = p
        }
        @Suppress("UNCHECKED_CAST")
        val checkedParams = nonNullParams as Array<Class<*>>
        val sig = buildString {
            append(clazz.name).append('.').append(methodName).append('(')
            for (p in checkedParams) append(p.name).append(';')
            append(')')
        }
        synchronized(lock) {
            if (methodCache.containsKey(sig)) {
                return methodCache[sig]
            }
        }

        var curr: Class<*>? = clazz
        while (curr != null) {
            try {
                val m = curr.getDeclaredMethod(methodName, *checkedParams)
                m.isAccessible = true
                synchronized(lock) {
                    methodCache[sig] = m
                }
                return m
            } catch (_: NoSuchMethodException) {
                curr = curr.superclass
            }
        }
        synchronized(lock) {
            methodCache[sig] = null
        }
        return null
    }

    fun clear() {
        synchronized(lock) {
            fieldCache.clear()
            methodCache.clear()
            classCache.clear()
        }
    }
}
