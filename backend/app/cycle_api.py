"""Machine credentials for n8n, separate local operator controls, compact status."""
import hmac
import asyncio
import ipaddress
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, ValidationError
from typing import Literal
from app.cycle_contracts import CycleRequest
from app.sec_api import write_access


class AgendaControl(BaseModel):
    model_config = ConfigDict(extra='forbid')
    owner: Literal['disabled','n8n']


def router(service):
    api = APIRouter()

    def machine(request):
        token = service.settings.token()
        if not token:
            raise HTTPException(503,'CYCLE_AUTH_NOT_CONFIGURED')
        try:
            local = ipaddress.ip_address(request.client.host).is_loopback
        except (ValueError,AttributeError):
            local = False
        if (not local or request.headers.get('origin') is not None or
                not hmac.compare_digest(request.headers.get('authorization','').encode(),('Bearer '+token).encode())):
            raise HTTPException(403,'CYCLE_AUTH_DENIED')

    request_schema = CycleRequest.model_json_schema()
    request_schema['properties']['budget'] = request_schema.pop('$defs')['Budget']

    @api.post('/api/cycles',status_code=202,openapi_extra={'requestBody':{'required':True,
        'content':{'application/json':{'schema':request_schema}}}})
    async def submit(request:Request,response:Response):
        machine(request)
        raw = bytearray()
        async for part in request.stream():
            raw.extend(part)
            if len(raw)>4096:
                raise HTTPException(413,'CYCLE_REQUEST_TOO_LARGE')
        try:
            body = CycleRequest.model_validate_json(raw)
        except ValidationError:
            raise HTTPException(422,'INVALID_CYCLE_REQUEST') from None
        try:
            cycle,duplicate = await asyncio.to_thread(service.submit,body)
        except ValueError as error:
            raise HTTPException(409,str(error)) from None
        response.status_code = 200 if duplicate else 202
        return dict(cycle=cycle,duplicate=duplicate)

    @api.get('/api/cycles/{ident}')
    def get(ident:str,request:Request):
        machine(request)
        try:
            return service.get(ident)
        except KeyError:
            raise HTTPException(404,'CYCLE_NOT_FOUND') from None

    @api.get('/api/automation/status')
    def status():
        return service.status()

    @api.post('/api/universe/automation/control')
    def control(body:AgendaControl,request:Request):
        write_access(request)
        try:
            return service.set_owner(body.owner)
        except ValueError as error:
            raise HTTPException(409,str(error)) from None

    @api.post('/api/universe/automation/cycles/{ident}/cancel')
    def cancel(ident:str,request:Request):
        write_access(request)
        try:
            return service.cancel(ident)
        except KeyError:
            raise HTTPException(404,'CYCLE_NOT_FOUND') from None

    return api
