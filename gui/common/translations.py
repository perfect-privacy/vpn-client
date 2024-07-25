
import gettext, sys, os

from config.paths import APP_DIR


class Translations():
    def __init__(self, language, template_env):
        self.language = language
        self.template_env = template_env
        self.translations = {}
        for locale in ["de", "en"]:
            self.translations[locale] = gettext.translation('translations_%s' % locale, os.path.abspath(os.path.join(APP_DIR, 'locales')), fallback=False, languages=[locale])

        self._install()

    def update(self, language):
        self.language = language
        self._install()

    def _install(self):
        self.translations[self.language].install()
        self.template_env.add_extension('jinja2.ext.i18n')
        self.template_env.install_gettext_translations(self.translations[self.language], newstyle=True)
