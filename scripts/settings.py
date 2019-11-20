import yaml
from typing import List, Dict
import typing
from schema import Schema, Optional


class Settings:

    def __init__(self, path: str) -> None:
        self.__read_from(path)

    def __read_from(self, path: str) -> None:
        settings_schema = Schema({
            Optional('history', default={}): {str: str},
            Optional('upstream', default=None): {
                'type': lambda s: s in ['pypi', 'github'],
                'name': str,
            }
        })

        try:
            with open(path) as f:
                settings = yaml.safe_load(f)
            self._settings = settings_schema.validate(settings)
        except FileNotFoundError:
            self._settings = settings_schema.validate({})

    @property
    def namcap_excluded_lines(self) -> List[str]:
        return self._settings['namcap']['exclude_lines']

    @property
    def history(self) -> Dict[str, str]:
        return self._settings['history']

    @property
    def upstream(self) -> typing.Optional[Dict[str, str]]:
        return self._settings['upstream']
