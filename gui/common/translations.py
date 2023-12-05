
import gettext
class Translate():
    def __init__(self, language, template_env):
        self.language = language
        self.template_env = template_env

        self.translations = {
            "en": gettext.translation('translations_en', 'locales', fallback=False, languages=['en']),
            "de": gettext.translation('translations_de', 'locales', fallback=False, languages=['de']),
        }
        self._install()

    def update(self, language):
        self.language = language
        self._install()
        
    def _install(self):
        self.translations[self.language].install()
        self.template_env.add_extension('jinja2.ext.i18n')
        self.template_env.install_gettext_translations(self.translations[self.language], newstyle=True)
