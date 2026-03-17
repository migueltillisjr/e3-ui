import os
from jinja2 import Template

def load_prompt(filename: str, context: dict = None) -> str:
    base_dir = os.path.dirname(__file__)
    template_path = os.path.join(base_dir, 'prompts', filename)
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    if context:
        template = Template(template_content)
        return template.render(**context)

    return template_content
