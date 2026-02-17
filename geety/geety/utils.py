def get_nested_value(obj, key_path):
    current = obj
    parts = key_path.split('.')
    for part in parts:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return None
        elif isinstance(current, list):
            if len(current) > abs(int(part)):
                current = current[int(part)]
            else:
                return None
        else:
            try:
                current = getattr(current, part)
            except AttributeError:
                try:
                    current = current[part]
                except Exception:
                    return None
    return current


def list_strip(lst):
    if not lst:
        return []

    start = 0
    while start < len(lst) and type(lst[start]) is str and lst[start].isspace():
        start += 1
    
    end = len(lst) - 1
    while end >= 0 and type(lst[end]) is str and lst[end].isspace():
        end -= 1
    
    return lst[start : end + 1] if end >= start else []


def merge_dicts(sec, pri):
    for key, value in pri.items():
        if value is None and key in sec:
            continue
        sec[key] = value
