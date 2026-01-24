def typemap(
    _dict: dict,
    _types: dict | None) -> dict:
        if not _types:
            return _dict.copy()
        _dict = _dict.copy()
        for _key, _type in _types.items():
            _dict[_key] = _type(_dict[_key])
        return _dict
