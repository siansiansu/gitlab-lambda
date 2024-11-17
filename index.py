import json
import os
import base64
from typing import Dict, Any
from urllib.parse import parse_qs
import urllib.request
import urllib.parse

def create_response(status_code: int, message: str) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "response_type": "in_channel",
            "text": message
        })
    }

def handler(event, context):
    try:
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
        else:
            body = event.get('body', '')
            
        params = dict(parse_qs(body))
        text = params.get('text', [''])[0].strip()
        command = params.get('command', [''])[0].strip()
        user = params.get('user_id', [''])[0]
        
        if not text:
            return create_response(400, "Service name is required")
            
        service_name = text.split()[0]
        action = command.lstrip('/')
        
        boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
        data = []
        
        form_data = {
            'token': os.environ['PIPELINE_TOKEN'],
            'ref': 'main',
            'variables[ENV]': 'staging',
            'variables[USER_ID]': user,
            'variables[SERVICE]': service_name,
            'variables[ACTION]': action
        }
        
        for key, value in form_data.items():
            data.append(f'--{boundary}')
            data.append(f'Content-Disposition: form-data; name="{key}"')
            data.append('')
            data.append(value)
        data.append(f'--{boundary}--')
        
        body = '\r\n'.join(data).encode('utf-8')
        
        url = f"{os.environ.get('GITLAB_URL', 'https://gitlab.com')}/api/v4/projects/{os.environ['GITLAB_PROJECT_ID']}/trigger/pipeline"
        
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        
        request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read())
            pipeline_id = result.get('id')
            return create_response(200, f"200 OK")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, str(e))
