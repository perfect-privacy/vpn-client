import os

for lang in ["de", "en"]:
    print(lang)
    cmd = "msgfmt -o locales/%s/LC_MESSAGES/translations_%s.mo locales/%s/LC_MESSAGES/translations_%s.po" % (lang, lang, lang, lang)
    print(cmd)
    os.system(cmd)