# fmt: off
STRINGS = {
    "ru": {
        # --- Categories ---
        "category_chat": "Чаты",
        "category_chat_elements": "Элементы чата",
        "category_emoji": "Эмодзи и стикеры",
        "category_profile": "Профиль",
        "category_interface": "Интерфейс",
        "category_about": "О плагине",

        "plugin_description": "Убирает платные и лишние функции из Telegram",

        # --- Settings Menu ---
        "settings_options": "Меню настроек",
        "hide_premium_row": "«Telegram Premium»",
        "hide_stars_row": "«Мои Звёзды»",
        "hide_wallet_row": "«Кошелёк»",
        "hide_business_row": "«Telegram для бизнеса»",
        "hide_send_a_gift_row": "«Отправить подарок»",
        "hide_help_section": "Раздел «Помощь»",

        # --- Wallet ---
        "hide_wallet": "Скрыть «Кошелёк»",

        # --- Drawer Options ---
        "drawer_options": "Боковое меню",
        "manage_drawer_options": "Настроить боковое меню",

        # --- Chat List ---
        "chat_list": "Список чатов",
        "hide_stories": "Скрыть истории",
        "hide_action_bar_status": "Скрыть статус",
        "hide_greeting_button": "Скрыть приветствие Telegram Business",
        "greeting_info": "Убирает кнопку «установил(а) это сообщение для всех новых чатов» в пустых чатах",
        "hide_communities": "Скрыть сообщества",
        "hide_communities_default": "Не скрывать",
        "hide_communities_all": "Скрыть полностью",
        "hide_communities_badges_only": "Только возле аватарки",
        "hide_communities_profile_only": "Только в профиле",

        # --- Action Bar ---
        "action_bar": "Три точки",
        "hide_action_bar_live_stream": "Скрыть «Начать трансляцию» и «Видеочат»",
        "hide_action_bar_archived_stories": "Скрыть «Архив историй»",
        "hide_action_bar_send_gift": "Скрыть «Отправить подарок»",
        "hide_action_bar_boost_group": "Скрыть «Голоса»",
        "hide_action_bar_add_shortcut": "Скрыть «Создать ярлык»",
        "hide_action_bar_report": "Скрыть «Пожаловаться»",
        "hide_action_bar_clear_history": "Скрыть «Очистить историю»",

        # --- Chat Elements ---
        "gifts": "Подарки и деньги",
        "hide_bottom_gift_button": "Скрыть кнопку подарка в поле ввода",
        "hide_gift_cards": "Скрыть карточки подарков",
        "hide_giveaway_cards": "Скрыть розыгрыши",
        "hide_transfer_cards": "Скрыть карточки переводов",
        "hide_star_reaction": "Скрыть реакции за звёзды",

        "chat_input": "Поле ввода/Меню вложений",
        "hide_articles_editor": "Скрыть редактор статей",
        "simplified_articles_editor": "Упрощённый редактор статей",
        "hide_todo_button": "Скрыть списки задач",

        # --- AI Features ---
        "ai_features_header": "ИИ",
        "hide_ai_button": "Скрыть кнопку «AI»",
        "hide_ai_summarize": "Скрыть кнопку саммари",

        # --- Emoji & Stickers ---
        "premium_emoji_settings_header": "Кастомные эмодзи",
        "hide_premium_emoji_keyboard": "В клавиатуре",
        "hide_premium_emoji_reactions": "В реакциях",
        "hide_premium_search": "В поиске",
        "hide_premium_suggestions": "В подсказках",
        "premium_stickers_settings_header": "Премиум-стикеры",
        "hide_premium_stickers_recent": "В недавних",
        "hide_premium_stickers_search": "В поиске",
        "hide_premium_stickers_grid": "На панели выбора",
        "sticker_panel_header": "Панель стикеров",
        "hide_group_stickers": "Скрыть стикерпак группы",
        "hide_emoji_search": "Скрыть категории стикеров",
        "emoji_search_info": "Убирает полоску с паками и поиском под панелью стикеров",

        # --- Profile Buttons ---
        "profile_buttons": "Кнопки в профиле",
        "hide_profile_actions_gift_button": "Скрыть кнопку подарка",
        "hide_profile_actions_stories_button": "Скрыть кнопку историй",
        "hide_profile_actions_stream_button": "Скрыть кнопки трансляции и видеочата",
        "hide_profile_send_money": "Скрыть «Отправить деньги»",

        # --- Profile Tabs ---
        "profile_tabs": "Вкладки в профиле",
        "hide_stories_tab": "Скрыть «Истории»",
        "hide_gifts_tab": "Скрыть «Подарки»",

        # --- Profile Appearance ---
        "profile_appearance": "Оформление профиля",
        "manage_reply_elements": "Настроить оформление ответов",
        "hide_profile_background_emoji": "Скрыть фоновые эмодзи",
        "hide_profile_pinned_gifts": "Скрыть подарки вокруг аватара",
        "profile_appearance_info": "Эмодзи и подарки вокруг аватара",
        "hide_profile_colorful_background": "Скрыть цветной фон",
        "hide_profile_editor_gifts": "Скрыть подарки в редакторе оформления",
        "profile_editor_gifts_info": "В меню выбора цвета и фонового эмодзи",
        "hide_boost_badge": "Скрыть значок буста",
        "hide_premium_badge": "Скрыть значок Premium",
        "premium_badge_info": "Заодно отключает видеоаватары в списке чатов и в чате",
        "hide_bot_verification": "Скрыть значок верификации от организации",
        "hide_profile_music": "Скрыть трек",
        "hide_profile_business": "Скрыть данные бизнеса",
        "profile_business_info": "Геолокация и часы работы",
        "hide_profile_balance": "Скрыть баланс в профиле",
        "hide_collectible_status": "Скрыть collectible-статус",
        "collectible_status_info": "Если в статусе стоит подарок",
        "hide_stars_rating": "Скрыть рейтинг звёзд",

        # --- Premium Features ---
        "premium_features_header": "Премиум-функции",
        "hide_premium_features": "Скрыть премиум-функции",
        "premium_features_info": "Часть настроек конфиденциальности, теги папок и перевод чатов",

        # --- Chat Money ---
        "hide_chat_send_money": "Скрыть «Отправить деньги» в чате",

        # --- About Plugin ---
        "about_plugin": "О плагине",
        "github_repository": "Репозиторий на GitHub (поставь ⭐!)",
        "github_sub": "Без телеметрии. Модульная архитектура на Python, свой скрипт сборки, "
                      "Ruff-линтинг и стабы типов для java, xposed и android",

        "enable_debug_logs": "Логи плагина",

        # --- Bulletins ---
        "restart_required": "Перезапустите приложение, чтобы применить изменения.",
        "restart": "ПЕРЕЗАПУСТИТЬ",
    },
    "en": {
        # --- Categories ---
        "category_chat": "Chats",
        "category_chat_elements": "Chat elements",
        "category_emoji": "Emoji and stickers",
        "category_profile": "Profile",
        "category_interface": "Interface",
        "category_about": "About",

        "plugin_description": "Removes paid and bloated features from Telegram",

        # --- Settings Menu ---
        "settings_options": "Settings menu",
        "hide_premium_row": "«Telegram Premium»",
        "hide_stars_row": "«My Stars»",
        "hide_wallet_row": "«Wallet»",
        "hide_business_row": "«Telegram Business»",
        "hide_send_a_gift_row": "«Send a Gift»",
        "hide_help_section": "«Help» section",

        # --- Wallet ---
        "hide_wallet_drawer": "Hide «Wallet» in the side menu",
        "hide_wallet_attach": "Hide «Wallet» in the attachment menu",

        # --- Drawer Options ---
        "drawer_options": "Side menu",
        "manage_drawer_options": "Manage side menu",

        # --- Chat List ---
        "chat_list": "Chat list",
        "hide_stories": "Hide stories",
        "hide_action_bar_status": "Hide status",
        "hide_greeting_button": "Hide the Telegram Business greeting",
        "greeting_info": "Removes the «set this message for all new chats» button in empty chats",
        "hide_communities": "Hide communities",
        "hide_communities_default": "Don't hide",
        "hide_communities_all": "Hide completely",
        "hide_communities_badges_only": "Only at the avatar",
        "hide_communities_profile_only": "Only in the profile",

        # --- Action Bar ---
        "action_bar": "Three-dot menu",
        "hide_action_bar_live_stream": "Hide «Start Live Stream» and «Video Chat»",
        "hide_action_bar_archived_stories": "Hide «Archived Stories»",
        "hide_action_bar_send_gift": "Hide «Send a Gift»",
        "hide_action_bar_boost_group": "Hide «Boost Group»",
        "hide_action_bar_add_shortcut": "Hide «Add to Home Screen»",
        "hide_action_bar_report": "Hide «Report»",
        "hide_action_bar_clear_history": "Hide «Clear History»",

        # --- Chat Elements ---
        "gifts": "Gifts and money",
        "hide_bottom_gift_button": "Hide the gift button in the input field",
        "hide_gift_cards": "Hide gift cards",
        "hide_giveaway_cards": "Hide giveaways",
        "hide_transfer_cards": "Hide transfer cards",
        "hide_star_reaction": "Hide paid reactions",

        "chat_input": "Input field / Attachment menu",
        "hide_articles_editor": "Hide the articles editor",
        "simplified_articles_editor": "Simplified articles editor",
        "hide_todo_button": "Hide to-do lists",

        # --- AI Features ---
        "ai_features_header": "AI",
        "hide_ai_button": "Hide the AI button",
        "hide_ai_summarize": "Hide the summarize button",

        # --- Emoji & Stickers ---
        "premium_emoji_settings_header": "Custom emoji",
        "hide_premium_emoji_keyboard": "In the keyboard",
        "hide_premium_emoji_reactions": "In reactions",
        "hide_premium_search": "In search",
        "hide_premium_suggestions": "In suggestions",
        "premium_stickers_settings_header": "Premium stickers",
        "hide_premium_stickers_recent": "In recents",
        "hide_premium_stickers_search": "In search",
        "hide_premium_stickers_grid": "In the picker",
        "sticker_panel_header": "Sticker panel",
        "hide_group_stickers": "Hide the group sticker pack",
        "hide_emoji_search": "Hide sticker categories",
        "emoji_search_info": "Removes the strip with packs and search under the sticker panel",

        # --- Profile Buttons ---
        "profile_buttons": "Profile buttons",
        "hide_profile_actions_gift_button": "Hide the gift button",
        "hide_profile_actions_stories_button": "Hide the stories button",
        "hide_profile_actions_stream_button": "Hide the live stream and video chat buttons",
        "hide_profile_send_money": "Hide «Send Money» in the profile",

        # --- Profile Tabs ---
        "profile_tabs": "Profile tabs",
        "hide_stories_tab": "Hide «Stories»",
        "hide_gifts_tab": "Hide «Gifts»",

        # --- Profile Appearance ---
        "profile_appearance": "Profile appearance",
        "manage_reply_elements": "Customize reply appearance",
        "hide_profile_background_emoji": "Hide background emoji",
        "hide_profile_pinned_gifts": "Hide gifts around the avatar",
        "profile_appearance_info": "Emoji and gifts around the avatar",
        "hide_profile_colorful_background": "Hide the colorful background",
        "hide_profile_editor_gifts": "Hide gifts in the appearance editor",
        "profile_editor_gifts_info": "In the color and background emoji picker",
        "hide_boost_badge": "Hide the boost badge",
        "hide_premium_badge": "Hide the Premium badge",
        "premium_badge_info": "Also disables video avatars in the chat list and in chats",
        "hide_bot_verification": "Hide the organization verification badge",
        "hide_profile_music": "Hide the music track",
        "hide_profile_business": "Hide business info",
        "profile_business_info": "Location and working hours",
        "hide_profile_balance": "Hide balance in the profile",
        "hide_collectible_status": "Hide the collectible status",
        "collectible_status_info": "If there's a gift in the status",
        "hide_stars_rating": "Hide the stars rating",

        # --- Premium Features ---
        "premium_features_header": "Premium features",
        "hide_premium_features": "Hide premium features",
        "premium_features_info": "Some privacy settings, folder tags, and chat translation",

        # --- Chat Money ---
        "hide_chat_send_money": "Hide «Send Money» in chats",

        # --- About Plugin ---
        "about_plugin": "About",
        "github_repository": "GitHub repository (leave a ⭐!)",
        "github_sub": "No telemetry. Modular Python architecture, a custom build script, "
                      "Ruff linting, and typing stubs for the java, xposed, and android modules.",

        "enable_debug_logs": "Plugin logging",

        # --- Bulletins ---
        "restart_required": "Restart the app to apply the changes.",
        "restart": "RESTART",
    }
}
# fmt: on
