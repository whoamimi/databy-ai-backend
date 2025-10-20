"""
app.agent.core.provider
"""

import ollama

from dataclasses import dataclass
from ...utils.settings import settings

def run_local(
    inputs: list[dict],
    model_id: str,
    options,
    host_url: str = settings.agent.server.ollama,
):
    client = ollama.Client(host_url)

    return client.chat(
        model=model_id,
        messages=inputs,
        stream=True,
        options=options,
    )

async def validate_model_exists(client, model_id: str):
    try:
        if m := client.show(model_id):
            print(f'Model ID: {model_id} pulled and ready to serve from ollama.\n{m}')
            return
    except ollama.ResponseError as e:
        print('Ollama Client Error while validating models existence', e)
        print(f'Current model: {client.list()} \nPulling model...')
        await client.pull(model_id)
        return await validate_model_exists(client, model_id)
    except Exception as e:
        raise e
