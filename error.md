^Croot@ubuntu-s-2vcpu-4gb-blr1-01:/opt/research-backend# docker compose logs -f
research_backend_api  | → fetching config.json
research_backend_api    | download: 's3://my-model-space/model/config.json' -> '/app/app/model/config.json' (2126 bytes in 0.0 seconds, 237.48 KB/s)
research_backend_api    | → fetching preprocessor_config.json
research_backend_api    | download: 's3://my-model-space/model/preprocessor_config.json' -> '/app/app/model/preprocessor_config.json' (212 bytes in 0.0 seconds, 28.16 KB/s)
research_backend_api    | → fetching vocab.json
research_backend_api    | download: 's3://my-model-space/model/vocab.json' -> '/app/app/model/vocab.json' (459 bytes in 0.0 seconds, 61.09 KB/s)
research_backend_api    | → fetching model.safetensors
research_backend_api    | download: 's3://my-model-space/model/model.safetensors' -> '/app/app/model/model.safetensors' (1261971480 bytes in 5.3 seconds, 229.20 MB/s)
research_backend_api    | [bootstrap] done.
research_backend_api    | INFO:     Started server process [1]
research_backend_api    | INFO:     Waiting for application startup.
research_backend_api    | Scheduler started. Daily analytics job scheduled for 03:00 Asia/Colombo.
research_backend_api    | INFO:     Application startup complete.
research_backend_api    | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
research_backend_api    | INFO:     172.18.0.3:51748 - "POST /analyze/both HTTP/1.1" 422 Unprocessable Entity
research_backend_api    | INFO:     172.18.0.3:43062 - "POST /phoneme/align HTTP/1.1" 422 Unprocessable Entity
research_backend_api    | INFO:     172.18.0.3:47300 - "GET /health HTTP/1.1" 200 OK
research_backend_api    | INFO:     172.18.0.3:54786 - "POST /gec/correct HTTP/1.1" 200 OK
research_backend_api    | INFO:     172.18.0.3:38748 - "POST /analyze/both HTTP/1.1" 422 Unprocessable Entity
research_backend_api    | [nltk_data] Downloading package averaged_perceptron_tagger_eng to
research_backend_api    | [nltk_data]     /root/nltk_data...
research_backend_api    | [nltk_data]   Unzipping taggers/averaged_perceptron_tagger_eng.zip.
research_backend_api    | INFO:     172.18.0.3:40790 - "POST /analyze/both HTTP/1.1" 200 OK
research_backend_caddy  | {"level":"info","ts":1757912767.6567812,"msg":"maxprocs: Leaving GOMAXPROCS=2: CPU quota undefined"}
research_backend_caddy  | {"level":"info","ts":1757912767.6571507,"msg":"GOMEMLIMIT is updated","package":"github.com/KimMachineGun/automemlimit/memlimit","GOMEMLIMIT":3691649433,"previous":9223372036854775807}
research_backend_caddy  | {"level":"info","ts":1757912767.6573083,"msg":"using config from file","file":"/etc/caddy/Caddyfile"}
research_backend_caddy  | {"level":"info","ts":1757912767.6594608,"msg":"adapted config to JSON","adapter":"caddyfile"}
research_backend_caddy  | {"level":"warn","ts":1757912767.659482,"msg":"Caddyfile input is not formatted; run 'caddy fmt --overwrite' to fix inconsistencies","adapter":"caddyfile","file":"/etc/caddy/Caddyfile","line":2}
research_backend_caddy  | {"level":"info","ts":1757912767.6607087,"logger":"admin","msg":"admin endpoint started","address":"localhost:2019","enforce_origin":false,"origins":["//localhost:2019","//[::1]:2019","//127.0.0.1:2019"]}
research_backend_caddy  | {"level":"warn","ts":1757912767.6609585,"logger":"http.auto_https","msg":"server is listening only on the HTTP port, so no automatic HTTPS will be applied to this server","server_name":"srv0","http_port":80}
research_backend_caddy  | {"level":"warn","ts":1757912767.6612618,"logger":"http","msg":"HTTP/2 skipped because it requires TLS","network":"tcp","addr":":80"}
research_backend_caddy  | {"level":"warn","ts":1757912767.6612723,"logger":"http","msg":"HTTP/3 skipped because it requires TLS","network":"tcp","addr":":80"}
research_backend_caddy  | {"level":"info","ts":1757912767.661275,"logger":"http.log","msg":"server running","name":"srv0","protocols":["h1","h2","h3"]}
research_backend_caddy  | {"level":"info","ts":1757912767.6615424,"msg":"autosaved config (load with --resume flag)","file":"/config/caddy/autosave.json"}
research_backend_caddy  | {"level":"info","ts":1757912767.6615553,"msg":"serving initial configuration"}
research_backend_caddy  | {"level":"info","ts":1757912767.6619046,"logger":"tls.cache.maintenance","msg":"started background certificate maintenance","cache":"0xc000602300"}
research_backend_caddy  | {"level":"info","ts":1757912767.663022,"logger":"tls","msg":"storage cleaning happened too recently; skipping for now","storage":"FileStorage:/data/caddy","instance":"44dde54a-3822-4c9d-b3fd-50dbacd8ab7f","try_again":1757999167.6630204,"try_again_in":86399.999999379}
research_backend_caddy  | {"level":"info","ts":1757912767.6631522,"logger":"tls","msg":"finished cleaning storage units"}
research_backend_api    | INFO:     172.18.0.3:52780 - "POST /analyze/both HTTP/1.1" 200 OK
research_backend_api    | INFO:     172.18.0.3:38106 - "POST /analyze/both HTTP/1.1" 500 Internal Server Error
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
research_backend_api    |   File "/app/app/main.py", line 161, in analyze_both
research_backend_api    |     phoneme_result = run_phoneme(audio, ref_text=text_to_use)
research_backend_api    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/utils_phone.py", line 170, in run_phoneme
research_backend_api    |     y, sr = sf.read(io.BytesIO(buf), dtype="float32", always_2d=False)
research_backend_api    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 285, in read
research_backend_api    |     with SoundFile(file, 'r', samplerate, channels,
research_backend_api    |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 658, in __init__
research_backend_api    |     self._file = self._open(file, mode_int, closefd)
research_backend_api    |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 1216, in _open
research_backend_api    |     raise LibsndfileError(err, prefix="Error opening {0!r}: ".format(self.name))
research_backend_api    | soundfile.LibsndfileError: Error opening <_io.BytesIO object at 0x7fe17d2c5a80>: Format not recognised.
research_backend_api    | INFO:     172.18.0.3:38114 - "GET /cgi-bin/luci/ HTTP/1.1" 404 Not Found
research_backend_api    | INFO:     172.18.0.3:38112 - "POST /analyze/both HTTP/1.1" 500 Internal Server Error
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
research_backend_api    |   File "/app/app/main.py", line 161, in analyze_both
research_backend_api    |     phoneme_result = run_phoneme(audio, ref_text=text_to_use)
research_backend_api    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/utils_phone.py", line 170, in run_phoneme
research_backend_api    |     y, sr = sf.read(io.BytesIO(buf), dtype="float32", always_2d=False)
research_backend_api    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 285, in read
research_backend_api    |     with SoundFile(file, 'r', samplerate, channels,
research_backend_api    |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 658, in __init__
research_backend_api    |     self._file = self._open(file, mode_int, closefd)
research_backend_api    |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 1216, in _open
research_backend_api    |     raise LibsndfileError(err, prefix="Error opening {0!r}: ".format(self.name))
research_backend_api    | soundfile.LibsndfileError: Error opening <_io.BytesIO object at 0x7fe17cc5af70>: Format not recognised.
research_backend_api    | INFO:     172.18.0.3:38114 - "POST /analyze/both HTTP/1.1" 500 Internal Server Error
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
research_backend_api    |   File "/app/app/main.py", line 161, in analyze_both
research_backend_api    |     phoneme_result = run_phoneme(audio, ref_text=text_to_use)
research_backend_api    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/utils_phone.py", line 170, in run_phoneme
research_backend_api    |     y, sr = sf.read(io.BytesIO(buf), dtype="float32", always_2d=False)
research_backend_api    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 285, in read
research_backend_api    |     with SoundFile(file, 'r', samplerate, channels,
research_backend_api    |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 658, in __init__
research_backend_api    |     self._file = self._open(file, mode_int, closefd)
research_backend_api    |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 1216, in _open
research_backend_api    |     raise LibsndfileError(err, prefix="Error opening {0!r}: ".format(self.name))
research_backend_api    | soundfile.LibsndfileError: Error opening <_io.BytesIO object at 0x7fe1808da7f0>: Format not recognised.
research_backend_api    | INFO:     172.18.0.3:35720 - "POST /analyze/both HTTP/1.1" 500 Internal Server Error
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
research_backend_api    |   File "/app/app/main.py", line 161, in analyze_both
research_backend_api    |     phoneme_result = run_phoneme(audio, ref_text=text_to_use)
research_backend_api    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/app/app/utils_phone.py", line 170, in run_phoneme
research_backend_api    |     y, sr = sf.read(io.BytesIO(buf), dtype="float32", always_2d=False)
research_backend_api    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 285, in read
research_backend_api    |     with SoundFile(file, 'r', samplerate, channels,
research_backend_api    |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 658, in __init__
research_backend_api    |     self._file = self._open(file, mode_int, closefd)
research_backend_api    |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/soundfile.py", line 1216, in _open
research_backend_api    |     raise LibsndfileError(err, prefix="Error opening {0!r}: ".format(self.name))
research_backend_api    | soundfile.LibsndfileError: Error opening <_io.BytesIO object at 0x7fe180c091c0>: Format not recognised.

