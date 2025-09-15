research_backend_api    | → fetching config.json
research_backend_api    | download: 's3://my-model-space/model/config.json' -> '/app/app/model/config.json' (2126 bytes in 0.0 seconds, 226.16 KB/s)
research_backend_api    | → fetching preprocessor_config.json
research_backend_api    | download: 's3://my-model-space/model/preprocessor_config.json' -> '/app/app/model/preprocessor_config.json' (212 bytes in 0.0 seconds, 46.50 KB/s)
research_backend_api    | → fetching vocab.json
research_backend_api    | download: 's3://my-model-space/model/vocab.json' -> '/app/app/model/vocab.json' (459 bytes in 0.0 seconds, 90.73 KB/s)
research_backend_api    | → fetching model.safetensors
research_backend_api    | download: 's3://my-model-space/model/model.safetensors' -> '/app/app/model/model.safetensors' (1261971480 bytes in 5.2 seconds, 232.55 MB/s)
research_backend_api    | [bootstrap] done.
research_backend_api    | INFO:     Started server process [1]
research_backend_api    | INFO:     Waiting for application startup.
research_backend_api    | Scheduler started. Daily analytics job scheduled for 03:00 Asia/Colombo.
research_backend_api    | INFO:     Application startup complete.
research_backend_api    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
research_backend_api    | INFO:     172.18.0.3:49998 - "GET /analytics/test123 HTTP/1.1" 500 Internal Server Error
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
research_backend_api    |   File "/app/app/main.py", line 79, in get_analytics
research_backend_api    |     return format_analytics_response(cached_data)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/main.py", line 58, in format_analytics_response
research_backend_api    |     "user_id": data["user_id"],
research_backend_api    |                ~~~~^^^^^^^^^^^
research_backend_api    |   File "lib/sqlalchemy/cyextension/resultproxy.pyx", line 54, in sqlalchemy.cyextension.resultproxy.BaseRow.__getitem__
research_backend_api    | TypeError: tuple indices must be integers or slices, not str
