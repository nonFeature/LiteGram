from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


# public void set(TL_stars.Tl_starsRating starsRating)
# just saying that user don't have any starsRating
class StarRatingViewSetHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            try:
                param.args[0] = None
            except IndexError:
                pass


def register_star_rating(plugin) -> None:
    StarRatingView = find_class("org.telegram.ui.Components.StarRatingView")
    if StarRatingView:
        plugin.hook_all_methods(StarRatingView, "set", StarRatingViewSetHook(plugin, Keys.hide_stars_rating))
