import os
import sys

lang = sys.argv[1]
cmd = 'msgattrib --untranslated locales/%s/LC_MESSAGES/translations_%s.po |grep -v "^#: "' % (lang, lang)
os.system(cmd)