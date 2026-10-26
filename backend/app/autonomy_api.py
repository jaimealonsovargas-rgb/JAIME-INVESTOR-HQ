from fastapi import APIRouter, Request, HTTPException
from app.autonomy_contracts import Control
from app.research_api import mutation


def router(service):
    api = APIRouter(prefix='/api/research/autonomy')

    def call(fn, *args):
        try:
            return fn(*args)
        except KeyError:
            raise HTTPException(404, 'NOT_FOUND') from None
        except ValueError as error:
            raise HTTPException(409, str(error)) from None

    @api.get('')
    async def status():
        return service.status()

    @api.post('/control')
    async def control(body: Control, request: Request):
        return call(service.control, body.action, mutation(request))

    @api.post('/tasks/{task_id}/cancel')
    async def cancel(task_id: str, request: Request):
        mutation(request)
        return call(service.cancel, task_id)

    return api
