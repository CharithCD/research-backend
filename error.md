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
research_backend_api    |   File "/app/app/main.py", line 81, in get_analytics
research_backend_api    |     return format_analytics_response(cached_data)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/main.py", line 58, in format_analytics_response
research_backend_api    |     data_dict = dict(data)
research_backend_api    |                 ^^^^^^^^^^
research_backend_api    | ValueError: dictionary update sequence element #0 has length 7; 2 is required

