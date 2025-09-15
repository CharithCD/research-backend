research_backend_api exited with code 1
research_backend_api    | ✓ config.json present; skip
research_backend_api    | ✓ preprocessor_config.json present; skip
research_backend_api    | ✓ vocab.json present; skip
research_backend_api    | ✓ model.safetensors present; skip
research_backend_api    | [bootstrap] done.
research_backend_api    | Traceback (most recent call last):
research_backend_api    |   File "/usr/local/bin/uvicorn", line 7, in <module>
research_backend_api    |     sys.exit(main())
research_backend_api    |              ^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/click/core.py", line 1442, in __call__
research_backend_api    |     return self.main(*args, **kwargs)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/click/core.py", line 1363, in main
research_backend_api    |     rv = self.invoke(ctx)
research_backend_api    |          ^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/click/core.py", line 1226, in invoke
research_backend_api    |     return ctx.invoke(self.callback, **ctx.params)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/click/core.py", line 794, in invoke
research_backend_api    |     return callback(*args, **kwargs)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/main.py", line 410, in main
research_backend_api    |     run(
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/main.py", line 577, in run
research_backend_api    |     server.run()
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 65, in run
research_backend_api    |     return asyncio.run(self.serve(sockets=sockets))
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
research_backend_api    |     return runner.run(main)
research_backend_api    |            ^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
research_backend_api    |     return self._loop.run_until_complete(task)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 69, in serve
research_backend_api    |     await self._serve(sockets)
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 76, in _serve
research_backend_api    |     config.load()
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/config.py", line 434, in load
research_backend_api    |     self.loaded_app = import_from_string(self.app)
research_backend_api    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 19, in import_from_string
research_backend_api    |     module = importlib.import_module(module_str)
research_backend_api    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
research_backend_api    |     return _bootstrap._gcd_import(name[level:], package, level)
research_backend_api    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
research_backend_api    |   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
research_backend_api    |   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
research_backend_api    |   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
research_backend_api    |   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
research_backend_api    |   File "<frozen importlib._bootstrap_external>", line 936, in exec_module
research_backend_api    |   File "<frozen importlib._bootstrap_external>", line 1074, in get_code
research_backend_api    |   File "<frozen importlib._bootstrap_external>", line 1004, in source_to_code
research_backend_api    |   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
research_backend_api    |   File "/app/app/main.py", line 164
research_backend_api    |     converted_audio = convert_audio_to_mono_wav(audio)
research_backend_api    | IndentationError: unexpected indent
