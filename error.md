research_backend_caddy  | {"level":"warn","ts":1757865190.2959104,"logger":"http","msg":"HTTP/2 skipped because it requires TLS","network":"tcp","addr":":80"}
research_backend_caddy  | {"level":"warn","ts":1757865190.2959223,"logger":"http","msg":"HTTP/3 skipped because it requires TLS","network":"tcp","addr":":80"}
research_backend_caddy  | {"level":"info","ts":1757865190.2959247,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
research_backend_caddy  | {"level":"info","ts":1757865190.2962973,"msg":"autosaved config (load with --resume flag)","file":"/config/caddy/autosave.json"}
research_backend_caddy  | {"level":"info","ts":1757865190.2963092,"msg":"serving initial configuration"}
research_backend_caddy  | {"level":"info","ts":1757865190.2967722,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0xc000230800"}
research_backend_caddy  | {"level":"info","ts":1757865190.2977986,"logger":"tls","msg":"storage cleaning happened too recently; skipping for now","storage":"FileStorage:/data/caddy","instance":"44dde54a-3822-4c9d-b3fd-50dbacd8ab7f","try_again":1757951590.2977972,"try_again_in":86399.999999474}
research_backend_caddy  | {"level":"info","ts":1757865190.297981,"logger":"tls","msg":"finished cleaning storage units"}
research_backend_api    | → fetching config.json
research_backend_api    | download: 's3://my-model-space/model/config.json' -> '/app/app/model/config.json' (2126 bytes in 0.0 seconds, 257.27 KB/s)
research_backend_api    | → fetching preprocessor_config.json
research_backend_api    | download: 's3://my-model-space/model/preprocessor_config.json' -> '/app/app/model/preprocessor_config.json' (212 bytes in 0.0 seconds, 28.50 KB/s)
research_backend_api    | → fetching vocab.json
research_backend_api    | download: 's3://my-model-space/model/vocab.json' -> '/app/app/model/vocab.json' (459 bytes in 0.0 seconds, 55.13 KB/s)
research_backend_api    | → fetching model.safetensors
research_backend_api    | download: 's3://my-model-space/model/model.safetensors' -> '/app/app/model/model.safetensors' (1261971480 bytes in 5.2 seconds, 233.09 MB/s)
research_backend_api    | [bootstrap] done.
research_backend_api    | INFO:     Started server process [1]
research_backend_api    | INFO:     Waiting for application startup.
research_backend_api    | INFO:     Application startup complete.
research_backend_api    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
research_backend_api    | INFO:     172.18.0.3:39636 - "POST /analyze/both HTTP/1.1" 500 Internal Server Error
research_backend_api    | ERROR:    Exception in ASGI application
research_backend_api    | Traceback (most recent call last):
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/protocols/http/httptools_impl.py", line 401, in run_asgi
research_backend_api    |     result = await app(  # type: ignore[func-returns-value]
research_backend_api    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/middleware/proxy_headers.py", line 70, in __call__
research_backend_api    |     return await self.app(scope, receive, send)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/fastapi/applications.py", line 1054, in __call__
research_backend_api    |     await super().__call__(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/applications.py", line 113, in __call__
research_backend_api    |     await self.middleware_stack(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 187, in __call__
research_backend_api    |     raise exc
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/errors.py", line 165, in __call__
research_backend_api    |     await self.app(scope, receive, _send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/cors.py", line 85, in __call__
research_backend_api    |     await self.app(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
research_backend_api    |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 62, in wrapped_app
research_backend_api    |     raise exc
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 51, in wrapped_app
research_backend_api    |     await app(scope, receive, sender)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 715, in __call__
research_backend_api    |     await self.middleware_stack(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 735, in app
research_backend_api    |     await route.handle(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 288, in handle
research_backend_api    |     await self.app(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 76, in app
research_backend_api    |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 62, in wrapped_app
research_backend_api    |     raise exc
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/_exception_handler.py", line 51, in wrapped_app
research_backend_api    |     await app(scope, receive, sender)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/starlette/routing.py", line 73, in app
research_backend_api    |     response = await f(request)
research_backend_api    |                ^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 301, in app
research_backend_api    |     raw_response = await run_endpoint_function(
research_backend_api    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/fastapi/routing.py", line 212, in run_endpoint_function
research_backend_api    |     return await dependant.call(**values)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/main.py", line 111, in analyze_both
research_backend_api    |     transcribed_text = await transcribe_audio_with_openai(audio)
research_backend_api    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/utils_openai.py", line 12, in transcribe_audio_with_openai
research_backend_api    |     client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
research_backend_api    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/openai/_client.py", line 334, in __init__
research_backend_api    |     super().__init__(
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/openai/_base_client.py", line 1426, in __init__
research_backend_api    |     self._client = http_client or AsyncHttpxClientWrapper(
research_backend_api    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/openai/_base_client.py", line 1323, in __init__
research_backend_api    |     super().__init__(**kwargs)
research_backend_api    | TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'
research_backend_api    | Task exception was never retrieved
research_backend_api    | future: <Task finished name='Task-5' coro=<AsyncClient.aclose() done, defined at /usr/local/lib/python3.11/site-packages/httpx/_client.py:1978> exception=AttributeError("'AsyncHttpxClientWrapper' object has no attribute '_state'")>
research_backend_api    | Traceback (most recent call last):
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/httpx/_client.py", line 1982, in aclose
research_backend_api    |     if self._state != ClientState.CLOSED:
research_backend_api    |        ^^^^^^^^^^^
research_backend_api    | AttributeError: 'AsyncHttpxClientWrapper' object has no attribute '_state'

