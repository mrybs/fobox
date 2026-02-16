import re
import html
from urllib.parse import quote
from geety import Component


VAR_PATTERN = re.compile(r'\$([\w\.]+)(@html|@url)?')  # \$[\w\.]+(?![@\w\.])
VAR_PATTERN_ESCAPE_HTML = re.compile(r'\$([\w\.]+)@html')
VAR_PATTERN_ESCAPE_URL = re.compile(r'\$([\w\.]+)@url')


def var_pattern_apply_content(content, context, page, prevs):
    context = context.copy()
    for var in VAR_PATTERN.findall(content):
        if issubclass(type(context.get(var)), Component):
            context[var] = context[var].render(page, context, prevs)

    def replacer(match):
        var = match.group(1)
        if match.group(2) == '@html':
            return html.escape(context[var])
        elif match.group(2) == '@url':
            return quote(context[var])
        else:
            return context[var]
    
    return VAR_PATTERN.sub(replacer, content)


if __name__ == '__main__':
    cont = {
        'var1': '<br/>',
        'var2': 'Привет, мир!/',
        'var3': 'Просто переменная <br/>'
    }
    print(var_pattern_apply_content('$var1@html', cont, None, None))
    print(var_pattern_apply_content('$var2@url', cont, None, None))
    print(var_pattern_apply_content('$var3', cont, None, None))
