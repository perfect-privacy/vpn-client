import os
import glob, re

files = [
    "gui/default/views/*.py",
    "gui/default/views/modals/*.py",
    "gui/default/templates/*.py",
]

def find_gettext_matches(file):
    content = open(file, "r").read()
    matches_with_lines = []
    matches = re.finditer(r'{{ *(?:_|gettext)\((\"|\')((?:(?!\1).)*)\1.*?\)}}', content, re.DOTALL)
    for match in matches:
        start_line = content[:match.start()].count('\n') + 1
        end_line = start_line + match.group(0).count('\n')
        line_descriptor = f"{start_line}"
        if end_line != start_line:
            line_descriptor += f"-{end_line}"
        matches_with_lines.append((start_line, end_line, match.group(2)))
    return matches_with_lines
def find_gettext():
    messages_in_use = {}
    for f in files:
        all_files = glob.glob(f)
        for file in all_files:
            matches = find_gettext_matches(file)
            for match in matches:
                if match not in messages_in_use:
                    messages_in_use[match[2]] = {}
                messages_in_use[match[2]][file] = [match[0], match[1]]
    return messages_in_use

def find_ngettext_matches(file):
    content = open(file, "r").read()
    matches_with_lines = []
    # Updated regex to capture both singular and plural forms for ngettext
    pattern = r'{{ *(?:ngettext)\((\"|\')((?:(?!\1).)*)\1, *(\"|\')((?:(?!\3).)*)\3.*?\)}}'
    matches = re.finditer(pattern, content, re.DOTALL)
    for match in matches:
        start_line = content[:match.start()].count('\n') + 1
        end_line = start_line + match.group(0).count('\n')
        line_descriptor = f"{start_line}"
        if end_line != start_line:
            line_descriptor += f"-{end_line}"
        # Include both singular and plural forms for ngettext
        matches_with_lines.append((start_line, end_line, match.group(2), match.group(4)))

    return matches_with_lines

def find_ngettext():
    messages_in_use = {}
    for f in files:
        all_files = glob.glob(f)
        for file in all_files:
            matches = find_ngettext_matches(file)
            for match in matches:
                if match not in messages_in_use:
                    messages_in_use[match[2]] = {}
                messages_in_use[match[2]][file] = [match[0], match[1], match[3]]
    return messages_in_use


data = []

messages_in_use = find_gettext()
for key in messages_in_use:
    for file in messages_in_use[key]:
        data.append("#: %s:%s" % (file,messages_in_use[key][file][0] ))
    data.append('msgid "%s"' % key.replace("\n","\\n"))
    data.append('msgstr ""')
    data.append("")

messages_in_use = find_ngettext()
for key in messages_in_use:
    for file in messages_in_use[key]:
        data.append("#: %s:%s" % (file,messages_in_use[key][file][0] ))
    data.append('msgid "%s"' % key.replace("\n","\\n"))
    data.append('msgid_plural "%s"' % messages_in_use[key][file][2].replace("\n","\\n"))
    data.append('msgstr[0] ""')
    data.append('msgstr[1] ""')
    data.append("")

with open("messages.po","w") as f:
    f.write("\n".join(data))

for lang in ["de", "en"]:
    os.system("msgmerge -F -N locales/%s/LC_MESSAGES/translations_%s.po messages.po > messages_%s.po" % (lang, lang, lang))
    if len(open("messages_%s.po" % lang,"r").read()) > 100:
        os.system("mv messages_%s.po  locales/%s/LC_MESSAGES/translations_%s.po" % (lang, lang, lang))
        os.system("rm locales/%s/LC_MESSAGES/translations_%s.mo 2>/dev/null" % (lang, lang))
        print("new po and mo files created: locales/%s/LC_MESSAGES/translations_%s.po" % (lang, lang) )

os.system("rm messages.po")