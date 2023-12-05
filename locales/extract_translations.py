import os

os.system("xgettext -L JavaScript -j -F -o messages.po gui/default/views/*.py gui/default/views/modals/*.py ")

for lang in ["de", "en"]:
    os.system("msgmerge -N locales/%s/LC_MESSAGES/translations_%s.po messages.po > messages_%s.po" % (lang, lang, lang))
    os.system("mv messages_%s.po  locales/%s/LC_MESSAGES/translations_%s.po" % (lang, lang, lang))
