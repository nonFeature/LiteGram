from hook_utils import find_class
from java.lang.reflect import Modifier

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


class PrivacySettingsActivityUpdateRowsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_privacy_voices, False):
            return
        instance = param.thisObject
        try:
            PrivacySettingsActivity = find_class("org.telegram.ui.PrivacySettingsActivity")
            if PrivacySettingsActivity is None:
                return
            voices_row_field = PrivacySettingsActivity.getDeclaredField("voicesRow")
            voices_row_field.setAccessible(True)
            voices_row = voices_row_field.getInt(instance)
            if voices_row != -1:
                row_count_field = PrivacySettingsActivity.getDeclaredField("rowCount")
                row_count_field.setAccessible(True)
                row_count = row_count_field.getInt(instance)

                fields = PrivacySettingsActivity.getDeclaredFields()
                valid_row_fields = []
                for field in fields:
                    if field.getType().toString() == "int" and "row" in field.getName().lower():
                        if not (field.getModifiers() & Modifier.STATIC):
                            field.setAccessible(True)
                            valid_row_fields.append(field)

                voices_row_field.setInt(instance, -1)
                for f in valid_row_fields:
                    val = f.getInt(instance)
                    if voices_row < val < row_count:
                        f.setInt(instance, val - 1)
                row_count_field.setInt(instance, row_count - 1)
        except Exception:
            pass


class PrivacySettingsActivityAddPremiumStarHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_privacy_pay, False):
            return
        text = param.args[0]
        if text:
            try:
                LocaleController = find_class("org.telegram.messenger.LocaleController")
                R = find_class("org.telegram.messenger.R")
                if LocaleController is not None and R is not None:
                    privacy_messages_str = LocaleController.getString("PrivacyMessages", R.string.PrivacyMessages)
                    if str(text) == str(privacy_messages_str):
                        SpannableStringBuilder = find_class("android.text.SpannableStringBuilder")
                        if SpannableStringBuilder is not None:
                            builder = SpannableStringBuilder(text)
                            param.setResult(builder)
            except Exception:
                pass


class PrivacyControlActivityUpdateRowsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_privacy_pay, False):
            return
        instance = param.thisObject
        try:
            PrivacyControlActivity = find_class("org.telegram.ui.PrivacyControlActivity")
            if PrivacyControlActivity is None:
                return
            rules_type_field = PrivacyControlActivity.getDeclaredField("rulesType")
            rules_type_field.setAccessible(True)
            rules_type = rules_type_field.getInt(instance)
            if rules_type == 10:  # PRIVACY_RULES_TYPE_MESSAGES
                pay_row_field = PrivacyControlActivity.getDeclaredField("payRow")
                pay_row_field.setAccessible(True)
                pay_row = pay_row_field.getInt(instance)
                if pay_row != -1:
                    row_count_field = PrivacyControlActivity.getDeclaredField("rowCount")
                    row_count_field.setAccessible(True)
                    row_count = row_count_field.getInt(instance)

                    fields = PrivacyControlActivity.getDeclaredFields()
                    valid_row_fields = []
                    for field in fields:
                        if field.getType().toString() == "int" and "row" in field.getName().lower():
                            if not (field.getModifiers() & Modifier.STATIC):
                                field.setAccessible(True)
                                valid_row_fields.append(field)

                    pay_row_field.setInt(instance, -1)
                    for f in valid_row_fields:
                        val = f.getInt(instance)
                        if pay_row < val < row_count:
                            f.setInt(instance, val - 1)
                    row_count_field.setInt(instance, row_count - 1)
        except Exception:
            pass


class FiltersSetupActivityUpdateRowsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_folder_tags, False):
            return
        instance = param.thisObject
        try:
            FiltersSetupActivity = find_class("org.telegram.ui.FiltersSetupActivity")
            if FiltersSetupActivity is None:
                return
            show_tags_row_field = FiltersSetupActivity.getDeclaredField("showTagsRow")
            show_tags_row_field.setAccessible(True)
            show_tags_row = show_tags_row_field.getInt(instance)
            if show_tags_row != -1:
                items_field = FiltersSetupActivity.getDeclaredField("items")
                items_field.setAccessible(True)
                items = items_field.get(instance)
                if items and show_tags_row < items.size():
                    if show_tags_row + 1 < items.size():
                        items.remove(items.get(show_tags_row + 1))
                    items.remove(items.get(show_tags_row))
                    if show_tags_row - 1 >= 0:
                        prev_item = items.get(show_tags_row - 1)
                        if prev_item:
                            try:
                                vt_field = prev_item.getClass().getField("viewType")
                                vt_field.setAccessible(True)
                                vt = vt_field.getInt(prev_item)
                                if vt in (3, 6):
                                    items.remove(show_tags_row - 1)
                            except Exception:
                                pass

                    show_tags_row_field.setInt(instance, -1)
                    try:
                        folder_tags_position_field = FiltersSetupActivity.getDeclaredField("folderTagsPosition")
                        folder_tags_position_field.setAccessible(True)
                        folder_tags_position_field.setInt(instance, -1)
                    except Exception:
                        pass

                    adapter_field = FiltersSetupActivity.getDeclaredField("adapter")
                    adapter_field.setAccessible(True)
                    adapter = adapter_field.get(instance)
                    if adapter:
                        adapter.notifyDataSetChanged()
        except Exception:
            pass


class FilterCreateActivityUpdateRowsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_folder_tags, False):
            return
        instance = param.thisObject
        try:
            FilterCreateActivity = find_class("org.telegram.ui.FilterCreateActivity")
            if FilterCreateActivity is None:
                return
            items_field = FilterCreateActivity.getDeclaredField("items")
            items_field.setAccessible(True)
            items = items_field.get(instance)
            if items:
                vt_preview = 9
                vt_color = 10
                try:
                    f_preview = FilterCreateActivity.getDeclaredField("VIEW_TYPE_HEADER_COLOR_PREVIEW")
                    f_preview.setAccessible(True)
                    val = f_preview.get(None)
                    if val is not None:
                        vt_preview = int(val)
                except Exception:
                    pass
                try:
                    f_color = FilterCreateActivity.getDeclaredField("VIEW_TYPE_COLOR")
                    f_color.setAccessible(True)
                    val = f_color.get(None)
                    if val is not None:
                        vt_color = int(val)
                except Exception:
                    pass

                LocaleController = find_class("org.telegram.messenger.LocaleController")
                R = find_class("org.telegram.messenger.R")
                if LocaleController is not None and R is not None:
                    info_str = str(LocaleController.getString("FolderTagColorInfo", R.string.FolderTagColorInfo))
                else:
                    info_str = ""

                i = items.size() - 1
                while i >= 0:
                    item = items.get(i)
                    if item:
                        view_type_field = item.getClass().getField("viewType")
                        view_type_field.setAccessible(True)
                        view_type = view_type_field.getInt(item)

                        if view_type in (vt_preview, vt_color):
                            items.remove(i)
                        elif view_type in (3, 6):  # VIEW_TYPE_SHADOW = 3, VIEW_TYPE_SHADOW_TEXT = 6
                            text_field = item.getClass().getField("text")
                            text_field.setAccessible(True)
                            text = text_field.get(item)
                            if text and str(text) == info_str:
                                items.remove(i)
                    i -= 1

                adapter_field = FilterCreateActivity.getDeclaredField("adapter")
                adapter_field.setAccessible(True)
                adapter = adapter_field.get(instance)
                if adapter:
                    adapter.notifyDataSetChanged()
        except Exception:
            pass


class ListAdapterOnCreateViewHolderHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_folder_tags, False):
            return

        holder = param.getResult()
        if holder:
            try:
                view = holder.itemView
                if view is not None:
                    class_name = view.getClass().getName()
                    if "HeaderCellColorPreview" in class_name or "PeerColorGrid" in class_name:
                        view.setVisibility(8)
                        lp = view.getLayoutParams()
                        if lp is not None:
                            lp.height = 0
                            lp.width = 0
                            view.setLayoutParams(lp)
            except Exception:
                pass


class ListAdapterOnBindViewHolderHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_folder_tags, False):
            return

        holder = param.args[0]
        if not holder:
            return

        try:
            view = holder.itemView
            if view is not None:
                class_name = view.getClass().getName()
                if "HeaderCellColorPreview" in class_name or "PeerColorGrid" in class_name:
                    view.setVisibility(8)
                    lp = view.getLayoutParams()
                    if lp is not None:
                        lp.height = 0
                        lp.width = 0
                        view.setLayoutParams(lp)
                    return

                view_type = holder.getItemViewType()
                if view_type in (3, 6):
                    adapter_instance = param.thisObject
                    FilterCreateActivity = find_class("org.telegram.ui.FilterCreateActivity")
                    if FilterCreateActivity is not None:
                        outer_field = adapter_instance.getClass().getDeclaredField("this$0")
                        outer_field.setAccessible(True)
                        outer_instance = outer_field.get(adapter_instance)

                        items_field = FilterCreateActivity.getDeclaredField("items")
                        items_field.setAccessible(True)
                        items = items_field.get(outer_instance)

                        position = param.args[1]
                        if items and position < items.size():
                            item = items.get(position)
                            if item:
                                text_field = item.getClass().getField("text")
                                text_field.setAccessible(True)
                                text = text_field.get(item)
                                if text:
                                    LocaleController = find_class("org.telegram.messenger.LocaleController")
                                    R = find_class("org.telegram.messenger.R")
                                    if LocaleController is not None and R is not None:
                                        info_str = str(LocaleController.getString("FolderTagColorInfo", R.string.FolderTagColorInfo))
                                        if str(text) == info_str:
                                            view.setVisibility(8)
                                            lp = view.getLayoutParams()
                                            if lp is not None:
                                                lp.height = 0
                                                lp.width = 0
                                                view.setLayoutParams(lp)
        except Exception:
            pass


class MessagesControllerIsTranslationsAutoEnabledHook(BaseHook):
    def before_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_language_translate, False):
            param.setResult(False)


class SettingsRegistryCreateEntriesHook(BaseHook):
    def after_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_language_translate, False):
            remove_extera_setting_entry(param.thisObject, "showTranslateChatButton")


class MessagesControllerConstructorHook(BaseHook):
    def after_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_folder_tags, False):
            instance = param.thisObject
            try:
                field = instance.getClass().getField("folderTags")
                field.setAccessible(True)
                field.setBoolean(instance, False)
            except Exception:
                pass


class MessagesControllerSetFolderTagsHook(BaseHook):
    def before_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_folder_tags, False):
            try:
                param.args[0] = False
            except Exception:
                pass


class UserConfigIsPremiumHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.plugin.get_setting(Keys.hide_folder_tags, False):
            return
        from java.lang import Thread

        for element in Thread.currentThread().getStackTrace():
            class_name = element.getClassName()
            if "FilterCreateActivity" in class_name:
                param.setResult(True)
                return


class GeneralPreferencesActivityFillItemsHook(BaseHook):
    def after_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_language_translate, False):
            arrayList = param.args[0]
            if arrayList:
                i = arrayList.size() - 1
                while i >= 0:
                    uitem = arrayList.get(i)
                    if uitem:
                        try:
                            val = -1
                            try:
                                val = uitem.getClass().getField("id").getInt(uitem)
                            except Exception:
                                try:
                                    val = uitem.getClass().getField("f1708id").getInt(uitem)
                                except Exception:
                                    pass
                            if val == 2:  # GeneralItem.SHOW_TRANSLATE_CHAT_BUTTON.getId()
                                arrayList.remove(i)
                        except Exception:
                            pass
                    i -= 1


def is_matching_entry(entry, alias_to_remove):
    if not entry:
        return False
    try:
        clazz = entry.getClass()
        fields = clazz.getDeclaredFields()
        for field in fields:
            if field.getName() == "guid":
                field.setAccessible(True)
                val = field.get(entry)
                if val == alias_to_remove:
                    return True
    except Exception:
        pass
    return False


def remove_extera_setting_entry(registry, alias_to_remove):
    try:
        entries_field = registry.getClass().getDeclaredField("entriesStringAlias")
        entries_field.setAccessible(True)
        entries_map = entries_field.get(registry)
        if entries_map:
            entries_map.remove(alias_to_remove)
    except Exception:
        pass

    try:
        prepared_field = registry.getClass().getDeclaredField("preparedEntries")
        prepared_field.setAccessible(True)
        prepared = prepared_field.get(registry)
        if prepared:
            prepared_class = prepared.getClass()
            class_name = prepared_class.getName()

            if "Map" in class_name:
                keys = list(prepared.keySet().toArray())
                for key in keys:
                    val = prepared.get(key)
                    if val:
                        val_class = val.getClass()
                        val_class_name = val_class.getName()
                        if "List" in val_class_name:
                            i = val.size() - 1
                            while i >= 0:
                                entry = val.get(i)
                                if is_matching_entry(entry, alias_to_remove):
                                    val.remove(i)
                                i -= 1
                        elif is_matching_entry(val, alias_to_remove):
                            prepared.remove(key)
            elif "List" in class_name:
                i = prepared.size() - 1
                while i >= 0:
                    entry = prepared.get(i)
                    if is_matching_entry(entry, alias_to_remove):
                        prepared.remove(i)
                    i -= 1
    except Exception:
        pass


def register_hide_premium_features(plugin) -> None:
    # 1. Privacy settings: voice messages
    try:
        PrivacySettingsActivity = find_class("org.telegram.ui.PrivacySettingsActivity")
        if PrivacySettingsActivity:
            plugin.hook_all_methods(PrivacySettingsActivity, "updateRows", PrivacySettingsActivityUpdateRowsHook(plugin))
            plugin.hook_all_methods(PrivacySettingsActivity, "addPremiumStar", PrivacySettingsActivityAddPremiumStarHook(plugin))
    except Exception:
        pass

    # 2. Privacy settings: paid messages
    try:
        PrivacyControlActivity = find_class("org.telegram.ui.PrivacyControlActivity")
        if PrivacyControlActivity:
            plugin.hook_all_methods(PrivacyControlActivity, "updateRows", PrivacyControlActivityUpdateRowsHook(plugin))
    except Exception:
        pass

    # 3. Folders setting: folder tags
    try:
        FiltersSetupActivity = find_class("org.telegram.ui.FiltersSetupActivity")
        if FiltersSetupActivity:
            plugin.hook_all_methods(FiltersSetupActivity, "updateRows", FiltersSetupActivityUpdateRowsHook(plugin))
    except Exception:
        pass

    # 4. Languages: translate chats
    try:
        MessagesController = find_class("org.telegram.messenger.MessagesController")
        if MessagesController:
            plugin.hook_all_methods(MessagesController, "isTranslationsAutoEnabled", MessagesControllerIsTranslationsAutoEnabledHook(plugin))
            plugin.hook_all_constructors(MessagesController, MessagesControllerConstructorHook(plugin))
            plugin.hook_all_methods(MessagesController, "setFolderTags", MessagesControllerSetFolderTagsHook(plugin))
            # Proactively update existing instances of MessagesController
            if plugin.get_setting(Keys.hide_folder_tags, False):
                for i in range(4):  # Support up to 4 accounts
                    try:
                        instance = MessagesController.getInstance(i)
                        if instance:
                            field = instance.getClass().getField("folderTags")
                            field.setAccessible(True)
                            field.setBoolean(instance, False)
                    except Exception:
                        pass
    except Exception:
        pass

    # 4.1 UserConfig isPremium hook
    try:
        UserConfig = find_class("org.telegram.messenger.UserConfig")
        if UserConfig:
            plugin.hook_all_methods(UserConfig, "isPremium", UserConfigIsPremiumHook(plugin))
    except Exception:
        pass

    # 4.2 GeneralPreferencesActivity fillItems hook
    try:
        GeneralPreferencesActivity = find_class("com.exteragram.messenger.preferences.GeneralPreferencesActivity")
        if GeneralPreferencesActivity:
            plugin.hook_all_methods(GeneralPreferencesActivity, "fillItems", GeneralPreferencesActivityFillItemsHook(plugin))
    except Exception:
        pass

    # 5. Extera Settings registry: showTranslateChatButton
    try:
        SettingsRegistry = find_class("com.exteragram.messenger.preferences.utils.SettingsRegistry")
        if SettingsRegistry:
            plugin.hook_all_methods(SettingsRegistry, "createEntriesIfNeeded", SettingsRegistryCreateEntriesHook(plugin))
            # Proactively remove if registry is already initialized
            registry = SettingsRegistry.getInstance()
            if registry:
                remove_extera_setting_entry(registry, "showTranslateChatButton")
    except Exception:
        pass

    # 6. Folder editing: folder color tag
    try:
        FilterCreateActivity = find_class("org.telegram.ui.FilterCreateActivity")
        if FilterCreateActivity:
            plugin.hook_all_methods(FilterCreateActivity, "updateRows", FilterCreateActivityUpdateRowsHook(plugin))

        ListAdapter = find_class("org.telegram.ui.FilterCreateActivity$ListAdapter")
        if ListAdapter:
            plugin.hook_all_methods(ListAdapter, "onCreateViewHolder", ListAdapterOnCreateViewHolderHook(plugin))
            plugin.hook_all_methods(ListAdapter, "onBindViewHolder", ListAdapterOnBindViewHolderHook(plugin))
    except Exception:
        pass
