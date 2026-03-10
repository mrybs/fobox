from slinn import TemplateProtocol
import shutil
import os.path


class Template(TemplateProtocol):
    @staticmethod
    def install(app_path: str, template_path: str):
        basename = os.path.basename(app_path)
        shutil.copyfile(f'{template_path}/app/app.py', f'{app_path}/app.py')
        shutil.copyfile(f'{template_path}/app/config.json', f'{app_path}/config.json')
        shutil.copytree(f'{template_path}/app/views', f'{app_path}/views')
        with open(f'{app_path}/__init__.py', 'w') as f:
            f.write(
                'from slinn.slinn_app_api import SlinnAppAPI\n'
                'import sys, importlib\n\n\n'
                'app = SlinnAppAPI(".", package=__package__)\n\n\n'
                f'if "{basename}.app" not in sys.modules.keys():\n'
                f'    from {basename}.app import dp\n'
                'else:\n'
                f'    dp = importlib.reload(sys.modules["{basename}.app"]).dp\n'
            )
