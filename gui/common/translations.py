
import gettext, sys, os
class Translations():
    def __init__(self, language, template_env):
        self.language = language
        self.template_env = template_env

        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))  # get the bundle dir if bundled or simply the __file__ dir if not bundled
        self.translations = {}
        for locale in ["de", "en"]:
            self.translations[locale] = gettext.translation('translations_%s' % locale, os.path.abspath(os.path.join(bundle_dir, 'locales')), fallback=False, languages=[locale])

        self._install()

    def update(self, language):
        self.language = language
        self._install()

    def _install(self):
        self.translations[self.language].install()
        self.template_env.add_extension('jinja2.ext.i18n')
        self.template_env.install_gettext_translations(self.translations[self.language], newstyle=True)
