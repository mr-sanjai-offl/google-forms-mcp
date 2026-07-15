import re

file_path = r's:\google-forms-mcp\src\google_forms_mcp\services\forms_service.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
content = re.sub(r'from google_forms_mcp\.infrastructure\.rate_limiter import RateLimiter\n', '', content)
content = re.sub(r'from google_forms_mcp\.infrastructure\.retry import with_retry\n', '', content)
content = content.replace(
    'from google_forms_mcp.models.form import (',
    'from google_forms_mcp.clients.forms_client import FormsClient\nfrom google_forms_mcp.models.form import ('
)

# 2. __init__
content = content.replace(
    'def __init__(self, forms_client: Any, rate_limiter: RateLimiter) -> None:',
    'def __init__(self, forms_client: FormsClient) -> None:'
)
content = content.replace(
    '        self._limiter = rate_limiter\n',
    ''
)
content = content.replace(
    '            rate_limiter: Rate limiter instance.\n',
    ''
)

# 3. Remove decorators and limiters
content = re.sub(r'^\s*@with_retry\(\)\n', '', content, flags=re.MULTILINE)
content = re.sub(r'^\s*self\._limiter\.acquire\([^\)]*\)\n', '', content, flags=re.MULTILINE)

# 4. API Calls
content = content.replace(
    'self._client.forms().create(body=body).execute()',
    'self._client.create(body=body)'
)
content = content.replace(
    'self._client.forms().get(formId=form_id).execute()',
    'self._client.get(form_id=form_id)'
)
content = content.replace(
    'self._client.forms().batchUpdate(formId=form_id, body=body).execute()',
    'self._client.batch_update(form_id=form_id, requests=body.get("requests", []))'
)
content = content.replace(
    'self._client.forms().setPublishSettings(\n                formId=form_id, body=body\n            ).execute()',
    'self._client.set_publish_settings(form_id=form_id, body=body)'
)
content = content.replace(
    'self._client.forms().responses().list(**kwargs).execute()',
    'self._client.list_responses(**kwargs)'
)
content = content.replace(
    'self._client.forms().responses().get(formId=form_id, responseId=response_id).execute()',
    'self._client.get_response(form_id=form_id, response_id=response_id)'
)
content = content.replace(
    '            self._client.forms()\n            .responses()\n            .get(formId=form_id, responseId=response_id)\n            .execute()',
    '            self._client.get_response(form_id=form_id, response_id=response_id)'
)
content = content.replace(
    '            self._client.forms()\n            .batchUpdate(formId=form_id, body=body)\n            .execute()',
    '            self._client.batch_update(form_id=form_id, requests=body.get("requests", []))'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
