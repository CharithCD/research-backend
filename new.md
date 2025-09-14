Yes—we can spec this so a coding agent can build it end-to-end. Below is a tight, copy-paste-friendly implementation plan for your FastAPI backend.

0) Goal (what to build)

Compute last 7 days analytics per user from your existing phoneme_results and grammar_results.

Call an OpenAI endpoint once per run to generate a short, personalized insight message + error highlights.

Persist both analytics and the LLM insight as a cache row.

Serve it via GET /analytics/{user_id}?window=7d.

Recompute on schedule (1×/day) and on write (optional hook after each new attempt).

1) DB schema (Alem­bic migration)
-- user_analytics_cache: numeric facts (7-day window)
CREATE TABLE IF NOT EXISTS user_analytics_cache (
  user_id              VARCHAR(64) PRIMARY KEY,
  window_label         VARCHAR(16) NOT NULL DEFAULT '7d',
  from_ts              TIMESTAMPTZ,
  to_ts                TIMESTAMPTZ,
  -- counts
  attempts_phoneme     INT NOT NULL DEFAULT 0,
  attempts_grammar     INT NOT NULL DEFAULT 0,
  -- pronunciation (lower = better)
  per_sle_avg          NUMERIC(6,2),
  per_sle_median       NUMERIC(6,2),
  -- grammar
  edits_per_100w_avg   NUMERIC(6,2),
  latency_ms_p50       INT,
  -- extracted lists
  top_phone_subs       JSONB,      -- e.g., [{"pair":"TH->T","count":12}, ...]
  top_grammar_errors   JSONB,      -- optional: if you classify edits
  -- presentation (generated via LLM)
  badge                VARCHAR(64),
  headline_msg         TEXT,
  -- caching
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at           TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_analytics_cache_expires
  ON user_analytics_cache (expires_at);


If you use MySQL 8: change JSONB→JSON, TIMESTAMPTZ→TIMESTAMP.

2) Data sources (ex­pected columns)

phoneme_results(user_id, created_at, per_sle, ops_raw JSON?)

grammar_results(user_id, created_at, final_text, edits JSON?, latency_ms)

If ops_raw doesn’t carry substitutions, you’ll still compute PER%/counts and skip confusions.

3) Aggregation logic (7-day window)

Window: [now() - 7 days, now()] (Asia/Colombo).

Metrics:

Pronunciation: avg(per_sle), median(per_sle), attempts_phoneme.

Grammar: edits_per_100w_avg = mean( len(edits) * 100 / max(1, word_count(final_text)) ), latency_ms_p50, attempts_grammar.

Top phoneme confusions: parse ops_raw → count "REF->HYP" pairs (top 5–10).

Badge heuristic (deterministic, no LLM):

badge = "Most Improved" if avg(per_sle) < 15 OR (avg decreased vs previous cache by ≥2 points). Else "Keep Going".

4) OpenAI insight (optional, 1 call per user per run)

Why: Turn numbers into one friendly sentence + 3 bullet “focus” items.

Prompt (system):

You are a concise learning coach. Output JSON only.
Keys: headline (<= 180 chars), focus (array of <=3 short items).
Tone: motivational but factual. No emojis.


User content (example):

{
  "window": "last_7_days",
  "user_id": "demo1",
  "pronunciation": {
    "avg_per_sle": 19.1,
    "median_per_sle": 19.2,
    "top_phone_subs": [{"pair":"TH->T","count":12},{"pair":"IH->IY","count":8}]
  },
  "grammar": {
    "edits_per_100w_avg": 7.7,
    "latency_ms_p50": 1476
  },
  "attempts": {"phoneme": 21, "grammar": 27},
  "badge": "Keep Going"
}


Response (target format):

{
  "headline": "Pronunciation error rate ~19% this week; keep practicing TH and IH sounds. Grammar edits ~8/100 words—steady progress.",
  "focus": [
    "Practice minimal pairs: TH vs T",
    "Slow down to reduce 1.5s response latency",
    "Aim for <15% PER next week"
  ]
}


Notes

Validate the LLM’s JSON. If parse fails or API errors, fallback to a deterministic headline assembled in code.

5) FastAPI surface (contracts)
GET /analytics/{user_id}

Returns cached analytics; recompute if expires_at <= now() or force=true.

Response

{
  "user_id": "demo1",
  "window": "7d",
  "range": {"from": "2025-09-08T00:00:00+05:30", "to": "2025-09-15T00:00:00+05:30"},
  "attempts": {"phoneme": 21, "grammar": 27},
  "pronunciation": {
    "avg_per_sle": 19.1,
    "median_per_sle": 19.2,
    "top_phone_subs": [{"pair":"TH->T","count":12}]
  },
  "grammar": {"edits_per_100w_avg": 7.7, "latency_ms_p50": 1476},
  "badge": "Keep Going",
  "headline_msg": "Pronunciation error rate ~19% this week...",
  "updated_at": "2025-09-14T22:56:00Z",
  "expires_at": "2025-09-15T22:56:00Z"
}

POST /analytics/{user_id}/recompute

Triggers recompute now (auth required). Returns the same shape.

6) Service flow (pseudocode)
WINDOW_DAYS = 7
CACHE_TTL_HOURS = 24
TZ = "Asia/Colombo"

async def compute_last7d(db, user_id: str) -> dict:
    end = now_tz(TZ)
    start = end - timedelta(days=WINDOW_DAYS)

    p = await repo.phoneme_last7d(db, user_id, start, end)   # [{per_sle, created_at, ops_raw}, ...]
    g = await repo.grammar_last7d(db, user_id, start, end)   # [{final_text, edits, latency_ms}, ...]

    attempts_phoneme = len(p); attempts_grammar = len(g)

    per_vals = [r.per_sle for r in p if r.per_sle is not None]
    per_avg = round(np.mean(per_vals), 2) if per_vals else None
    per_med = round(np.median(per_vals), 2) if per_vals else None

    edits100 = []
    latencies = []
    for r in g:
        edits = r.edits or []            # ensure list
        words = max(1, len((r.final_text or "").split()))
        edits100.append(len(edits) * 100.0 / words)
        if r.latency_ms is not None: latencies.append(r.latency_ms)

    edits_per_100w_avg = round(float(np.mean(edits100)), 2) if edits100 else None
    latency_ms_p50 = int(np.percentile(latencies, 50)) if latencies else None

    subs_counts = Counter()
    for r in p:
        for a,b in extract_sub_pairs(r.ops_raw):  # return list[tuple[str,str]]
            subs_counts[f"{a}->{b}"] += 1
    top_subs = [{"pair":k,"count":v} for k,v in subs_counts.most_common(5)]

    badge = "Most Improved" if (per_avg is not None and per_avg < 15) else "Keep Going"

    # LLM insight (optional)
    insight = await generate_insight_openai({
        "pronunciation":{"avg_per_sle":per_avg,"median_per_sle":per_med,"top_phone_subs":top_subs},
        "grammar":{"edits_per_100w_avg":edits_per_100w_avg,"latency_ms_p50":latency_ms_p50},
        "attempts":{"phoneme":attempts_phoneme,"grammar":attempts_grammar},
        "badge": badge
    })

    return {
      "user_id": user_id, "window_label":"7d",
      "from_ts": start, "to_ts": end,
      "attempts_phoneme": attempts_phoneme, "attempts_grammar": attempts_grammar,
      "per_sle_avg": per_avg, "per_sle_median": per_med,
      "edits_per_100w_avg": edits_per_100w_avg, "latency_ms_p50": latency_ms_p50,
      "top_phone_subs": top_subs, "top_grammar_errors": None,
      "badge": badge, "headline_msg": insight.headline if insight else default_headline(...),
      "updated_at": now_utc(), "expires_at": now_utc() + timedelta(hours=CACHE_TTL_HOURS)
    }


extract_sub_pairs(ops_raw): parse JSON list/dict; return (ref, hyp) for substitutions; be lenient.

generate_insight_openai(payload):

Uses gpt-4o-mini (or your preferred compact model).

Sends system + user JSON above; sets response_format={"type":"json_object"}.

Time out 5–8s; if error → None.

7) Caching & update strategy

On schedule (daily): recompute for all active users.

On write (optional): when a new phoneme_results/grammar_results row is inserted, enqueue a debounced recompute for that user_id (e.g., within 1–5 minutes) so the dashboard feels fresh.

On read: return row if expires_at > now(); else recompute synchronously.

8) Scheduler options (pick one)

APScheduler inside FastAPI:

Cron: 0 3 * * * UTC (= 8:30 AM Asia/Colombo) or choose your time.

systemd timer / cron calling a small CLI python -m app.jobs.recompute_all.

Celery / RQ if you already have Redis; otherwise skip (overkill for this).

9) Env & secrets
OPENAI_API_KEY=...
ANALYTICS_CACHE_TTL_HOURS=24
TIMEZONE=Asia/Colombo

10) API examples (ready for your app)

GET

GET /analytics/demo1?window=7d
Authorization: Bearer <token>


200

{
  "user_id":"demo1",
  "window":"7d",
  "attempts":{"phoneme":21,"grammar":27},
  "pronunciation":{"avg_per_sle":19.1,"median_per_sle":19.2,"top_phone_subs":[{"pair":"TH->T","count":12}]},
  "grammar":{"edits_per_100w_avg":7.7,"latency_ms_p50":1476},
  "badge":"Keep Going",
  "headline_msg":"Pronunciation error rate ~19% this week; keep practicing TH and IH sounds. Grammar edits ~8/100 words—steady progress.",
  "updated_at":"2025-09-14T17:26:00Z",
  "expires_at":"2025-09-15T17:26:00Z"
}


POST recompute

POST /analytics/demo1/recompute

11) Testing checklist

Seed 2–3 users with mixed data to verify windowing.

Force expires_at to past and ensure recompute occurs on read.

Kill OpenAI call → ensure fallback headline works.

If ops_raw empty → still returns valid payload (no confusions).


grammar:
id	user_id	text_sha256	input_text	raw_corrected	final_text	edits	guardrails	latency_ms	created_at
1	test123	256280170bddb8c80b69a139ed4a8531d15ae486ec9751adb0524ff1b4bcf2d8	We discussed about the plan on Poya day.	We discussed about the plan on Poya day.	We discussed about the plan on Poya day.	[{"type":"PREP","span_src":{"text":"discussed about","end_tok":3,"start_tok":1},"guardrail":{"policy":"suppress_autocorrect","reason":"Accepted SLE preposition use","rule_id":"SLE-PREP-001"},"replacement":"discussed"}]	[{"span":{"text":"discussed about","end_tok":3,"start_tok":1},"type":"PREP","policy":"suppress_autocorrect","reason":"Accepted SLE preposition use","rule_id":"SLE-PREP-001"},{"span":{"text":"Poya","end_tok":7,"start_tok":6},"type":"LEX","policy":"suppress_autocorrect","reason":"SLE cultural term","rule_id":"SLE-LEX-001"}]	2466	2025-09-10 06:20:22.453497+00
2	test123	ff99ba2e9c69c4e52d1b8e7ee0aaff88757be1adce04894ed09e836b9eec71e4	He was happy.	He was happy.	He was happy.	[]	[]	2366	2025-09-14 16:04:15.863083+00
3	test123	376b788909f5603aaa30abce97c132b8df0acaf8431ad0758a0184e390870e3d	In Java, everything is an object.	In Java, everything is an object.	In Java, everything is an object.	[]	[]	955	2025-09-14 16:09:47.445026+00
4	test123	6b6d0adda6cf52713faa4e496e1abc6843d9d3460af8698f77b33b9b6f4f4f1b	Java can be easily extended since it is based on the object model.	Java can be easily extended since it is based on the object model.	Java can be easily extended since it is based on the object model.	[]	[]	1379	2025-09-14 16:09:58.002789+00
5	test123	376b788909f5603aaa30abce97c132b8df0acaf8431ad0758a0184e390870e3d	In Java, everything is an object.	In Java, everything is an object.	In Java, everything is an object.	[]	[]	796	2025-09-14 16:11:06.179336+00
6	test123	6b6d0adda6cf52713faa4e496e1abc6843d9d3460af8698f77b33b9b6f4f4f1b	Java can be easily extended since it is based on the object model.	Java can be easily extended since it is based on the object model.	Java can be easily extended since it is based on the object model.	[]	[]	1476	2025-09-14 16:11:14.156459+00
7	test123	62a58f5cafb694387473369e2dfd106d9d46202b258e2e424aab2636adb55cfa	Unlike many other programming languages, when Java is compiled, it is not compiled into a platform-specific machine, rather into a platform-independent bytecode. This bytecode is distributed over the web and interpreted by the virtual machine on which platform it is being run on.	Unlike many other programming languages, when Java is compiled, it is not compiled into a platform-specific machine, rather into a platform-independent bytecode. This bytecode is distributed over the web and interpreted by the virtual machine on which platform it is being run on.	Unlike many other programming languages, when Java is compiled, it is not compiled into a platform-specific machine, rather into a platform-independent bytecode. This bytecode is distributed over the web and interpreted by the virtual machine on which platform it is being run on.	[]	[]	5851	2025-09-14 16:11:36.707732+00
8	test123	55dea1fd3fa0d5d6e96b91abd9420ece77e1bbdc476b109ae6bd538e8ae8510f	Java is designed to be easy to learn. If you understand the basic concept of OOP, Java, it would be easy to master.	Java is designed to be easy to learn. If you understand the basic concept of OOP, Java, it would be easy to master.	Java is designed to be easy to learn. If you understand the basic concept of OOP, Java, it would be easy to master.	[]	[]	2770	2025-09-14 16:11:45.923516+00
9	test123	4ca35fe6a87a508bd63ea612f6173b97404c51071bbdfffb469fda57bec04525	cho vá»›i cÃ´ng váº¥n Generates and Architecture New Tools á»•n chá»©c pháº£i phÃ´ máº¡t.	Generates and Architecture New Tools n chc phi phÃ´ mt.	Generates and Architecture New Tools n chc phi phÃ´ mt.	[{"type":"DEL","span_src":{"text":"cho vá»›i cÃ´ng váº¥n","end_tok":4,"start_tok":0},"replacement":""},{"type":"SUB","span_src":{"text":"á»•n chá»©c pháº£i","end_tok":12,"start_tok":9},"replacement":"n chc phi"},{"type":"SUB","span_src":{"text":"máº¡t.","end_tok":14,"start_tok":13},"replacement":"mt."}]	[]	4188	2025-09-14 16:11:57.84757+00
10	test123	cbd25bcc0c6de10de95f727e23e121371b9cd9a9351120e271194e70ecfd5a35	which makes the compiled code executable on many processors.	The compiled code is executable on many processors.	The compiled code is executable on many processors.	[{"type":"SUB","span_src":{"text":"which makes the","end_tok":3,"start_tok":0},"replacement":"The"},{"type":"VERB","span_src":{"text":"","end_tok":5,"start_tok":5},"replacement":"is"}]	[]	1468	2025-09-14 16:12:05.10925+00
11	test123	c67d9e5245555756f31a727b207c260057d8b0b947403f33c4c071fa5cca61b4	Being architecture-neutral and having no implementation-dependent aspect of the specification makes Java portable. Compiler in Java is written in C.	Being architecture-neutral and having no implementation-dependent aspect of the specification makes Java portable. compiler in Java is written in C.	Being architecture-neutral and having no implementation-dependent aspect of the specification makes Java portable. compiler in Java is written in C.	[{"type":"ORTH","span_src":{"text":"Compiler","end_tok":14,"start_tok":13},"replacement":"compiler"}]	[]	2400	2025-09-14 16:12:18.653384+00
12	test123	1f5150e8faf4e13dc10a694d527cdc007aaba7a254ad8f0a18550ec85c08a8a1	Just to give you a little excitement about java programming, I am going to give you a small convenient C programming hello world program. You can try it using demo link.	Just to give you a little excitement about java programming, I am going to give you a small convenient C programming hello world program. You can try it using the demo link.	Just to give you a little excitement about java programming, I am going to give you a small convenient C programming hello world program. You can try it using the demo link.	[{"type":"INS","span_src":{"text":"","end_tok":29,"start_tok":29},"replacement":"the"}]	[]	3666	2025-09-14 16:12:31.525662+00
13	test123	3c129e87709bfd277b0b333c028c2383515e5fb44d267922957cc243ca835910	The latest release of the Java Standard Edition is 8. With the advancement of Java and its widespread popularity, multiple configurations were built to suit various types of platforms.	With the advancement of Java and its widespread popularity, multiple configurations were built to suit various types of platforms.	With the advancement of Java and its widespread popularity, multiple configurations were built to suit various types of platforms.	[{"type":"DEL","span_src":{"text":"The latest release of the Java Standard Edition is 8.","end_tok":10,"start_tok":0},"replacement":""}]	[]	2599	2025-09-14 16:12:51.396544+00
14	test123	ab0b2ba9483b12bb3e6e62318a3013057f647529632196feb74b40743bd37918	This design feature allows the developers to construct interactive applications that can run smoothly.	This design feature allows the developers to construct interactive applications that can run smoothly.	This design feature allows the developers to construct interactive applications that can run smoothly.	[]	[]	1506	2025-09-14 16:13:00.121717+00
15	test123	c9f679e5a62905792cf60a746486faf76ea0c186631fee43e3a2506f3c9f0943	Java bytecode is translated on the fly to native machine instruction and is not stored anywhere.	Java bytecode is translated on the fly to native machine instruction and is not stored anywhere.	Java bytecode is translated on the fly to native machine instruction and is not stored anywhere.	[]	[]	1994	2025-09-14 16:13:09.716994+00
16	test123	43ee585e3c26626f203be0b407d95353c19a6627b4e9359a595ca23bf536560e	The development process is more rapid and analytical since the linking is an incremental and lightweight process.	The development process is more rapid and analytical since the linking is an incremental and lightweight process.	The development process is more rapid and analytical since the linking is an incremental and lightweight process.	[]	[]	1553	2025-09-14 16:13:17.013851+00
17	test123	a5573597ca162422a4b4697564aec3d8d4cbc0f310c36f7b52e5ec292992cf93	With the use of just in-time compilers, Java enables high performance.	With the use of just in-time compilers, Java enables high performance.	With the use of just in-time compilers, Java enables high performance.	[]	[]	1482	2025-09-14 16:13:23.012792+00
18	test123	0f75f6c19a0f0ad267128daea441aaf821f8be21273de42f06e57dc29d1147c3	Java is considered to be a more dynamic programming language.	Java is considered to be a more dynamic programming language.	Java is considered to be a more dynamic programming language.	[]	[]	1155	2025-09-14 16:13:28.549213+00
19	test123	8ea90fdf5e8f1520bfb31aaca8de25c9800d723bf508ae76a82f029431311069	Java programs can carry extensive amount of runtime information that can be used to verify and resolve access to objects on runtime.	Java programs can carry an extensive amount of runtime information that can be used to verify and resolve access to objects on runtime.	Java programs can carry an extensive amount of runtime information that can be used to verify and resolve access to objects on runtime.	[{"type":"INS","span_src":{"text":"","end_tok":4,"start_tok":4},"replacement":"an"}]	[]	2240	2025-09-14 16:13:40.49072+00
26	demo1	102da8fb1f843f9d34fb5f1f505458d4637c1c773c37c5256690770cd98e6b7e	Poya day is a holiday in Sri Lanka.	Poya day is a holiday in Sri Lanka.	Poya day is a holiday in Sri Lanka.	[]	[{"span":{"text":"Poya","end_tok":1,"start_tok":0},"type":"LEX","policy":"suppress_autocorrect","reason":"SLE cultural term","rule_id":"SLE-LEX-001"}]	1324	2025-09-14 16:34:10.245652+00
27	demo1	3ad63d897e9f216ef073c62fc8c3b660924f6a40cd7d465fbded1761fc5c7919	I enjoys playing cricket.	I enjoy playing cricket.	I enjoy playing cricket.	[{"type":"SUB","span_src":{"text":"enjoys","end_tok":2,"start_tok":1},"replacement":"enjoy"}]	[]	708	2025-09-14 16:34:14.024437+00
20	"test123
"	54a6034b0d117cb9c78f6205fff36e181d0f50973eb22cd7d0ceceb12dd203d7	We discussed about the plan yesterday.	We discussed the plan yesterday.	We discussed about the plan yesterday.	[{"type":"PREP","span_src":{"text":"discussed about","end_tok":3,"start_tok":1},"guardrail":{"policy":"suppress_autocorrect","reason":"Accepted SLE preposition use","rule_id":"SLE-PREP-001"},"replacement":"discussed"}]	[{"span":{"text":"discussed about","end_tok":3,"start_tok":1},"type":"PREP","policy":"suppress_autocorrect","reason":"Accepted SLE preposition use","rule_id":"SLE-PREP-001"}]	622	2025-09-14 16:32:39.791108+00
21	"test123
"	e47acdc798350c95be7a7c95ed2dfe91a5ba63218fcc136fd33ea9943171f4ab	He go to school yesterday.	He went to school yesterday.	He went to school yesterday.	[{"type":"SUB","span_src":{"text":"go","end_tok":2,"start_tok":1},"replacement":"went"}]	[]	593	2025-09-14 16:32:40.744469+00
22	test123	102da8fb1f843f9d34fb5f1f505458d4637c1c773c37c5256690770cd98e6b7e	Poya day is a holiday in Sri Lanka.	Poya day is a holiday in Sri Lanka.	Poya day is a holiday in Sri Lanka.	[]	[{"span":{"text":"Poya","end_tok":1,"start_tok":0},"type":"LEX","policy":"suppress_autocorrect","reason":"SLE cultural term","rule_id":"SLE-LEX-001"}]	1088	2025-09-14 16:32:42.135414+00
23	"test123
"	3ad63d897e9f216ef073c62fc8c3b660924f6a40cd7d465fbded1761fc5c7919	I enjoys playing cricket.	I enjoy playing cricket.	I enjoy playing cricket.	[{"type":"SUB","span_src":{"text":"enjoys","end_tok":2,"start_tok":1},"replacement":"enjoy"}]	[]	575	2025-09-14 16:32:43.090451+00
24	test123	54a6034b0d117cb9c78f6205fff36e181d0f50973eb22cd7d0ceceb12dd203d7	We discussed about the plan yesterday.	We discussed the plan yesterday.	We discussed about the plan yesterday.	[{"type":"PREP","span_src":{"text":"discussed about","end_tok":3,"start_tok":1},"guardrail":{"policy":"suppress_autocorrect","reason":"Accepted SLE preposition use","rule_id":"SLE-PREP-001"},"replacement":"discussed"}]	[{"span":{"text":"discussed about","end_tok":3,"start_tok":1},"type":"PREP","policy":"suppress_autocorrect","reason":"Accepted SLE preposition use","rule_id":"SLE-PREP-001"}]	810	2025-09-14 16:34:02.004859+00
25	test123	e47acdc798350c95be7a7c95ed2dfe91a5ba63218fcc136fd33ea9943171f4ab	He go to school yesterday.	He went to school yesterday.	He went to school yesterday.	[{"type":"SUB","span_src":{"text":"go","end_tok":2,"start_tok":1},"replacement":"went"}]	[]	674	2025-09-14 16:34:05.740097+00

phone:
id	user_id	audio_sha256	ref_text	pred_phones	ref_phones	ops_raw	per_strict	per_sle	created_at
1	test123	1d10dd322b3fe6286dac799df315dfd177c0d727cf7b2f8bdbb4020540a5437a	He was happy	["HH","IY","W","AA","Z","HH","AE","P","IY"]	["HH","IY","W","AA","Z","HH","AE","P","IY"]	[]	0	0	2025-09-10 06:24:53.83015+00
2	test123	1d10dd322b3fe6286dac799df315dfd177c0d727cf7b2f8bdbb4020540a5437a	He was happy	["HH","IY","W","AA","Z","HH","AE","P","IY"]	["HH","IY","W","AA","Z","HH","AE","P","IY"]	[]	0	0	2025-09-10 06:25:23.377179+00
3	test123	1d10dd322b3fe6286dac799df315dfd177c0d727cf7b2f8bdbb4020540a5437a	He was not happy	["HH","IY","W","AA","Z","HH","AE","P","IY"]	["HH","IY","W","AA","Z","N","AA","T","HH","AE","P","IY"]	[{"g":"N","i":5,"j":5,"p":null,"op":"D"},{"g":"AA","i":6,"j":5,"p":null,"op":"D"},{"g":"T","i":7,"j":5,"p":null,"op":"D"}]	25	25	2025-09-10 06:26:17.900066+00
4	test123	1d10dd322b3fe6286dac799df315dfd177c0d727cf7b2f8bdbb4020540a5437a	He was happy.	["HH","IY","W","AA","Z","HH","AE","P","IY"]	["HH","IY","W","AA","Z","HH","AE","P","IY","."]	[{"g":".","i":9,"j":9,"p":null,"op":"D"}]	10	10	2025-09-14 16:04:15.843907+00
5	test123	2734c23205ea40dd6477d3587c18ebe82b593adb6dd7dae8c1fd62b9f0f3a9fe	In Java, everything is an object.	["IH","N","JH","AW","EH","V","R","AH","TH","IH","NG","IH","Z","AE","N","AA","B","JH","EH","K","T"]	["IH","N","JH","AA","V","AH",",","EH","V","R","IY","TH","IH","NG","IH","Z","AE","N","AH","B","JH","EH","K","T","."]	[{"g":"AA","i":3,"j":3,"p":"AW","op":"S"},{"g":"V","i":4,"j":4,"p":null,"op":"D"},{"g":"AH","i":5,"j":4,"p":null,"op":"D"},{"g":",","i":6,"j":4,"p":null,"op":"D"},{"g":"IY","i":10,"j":7,"p":"AH","op":"S"},{"g":"AH","i":18,"j":15,"p":"AA","op":"S"},{"g":".","i":24,"j":21,"p":null,"op":"D"}]	28	28	2025-09-14 16:09:47.437758+00
6	test123	775a5c6a1108ba11aef66b59435f013911e4939bafd8c60c202d2e22d1fc92f7	Java can be easily extended since it is based on the object model.	["JH","AW","ER","K","AE","N","B","IY","IY","Z","AH","L","IY","IH","K","S","T","EH","N","D","AH","D","S","IH","N","S","IH","T","IH","Z","B","EY","S","T","AA","N","DH","AH","AA","B","JH","EH","K","T","M","AA","D","AH","L"]	["JH","AA","V","AH","K","AE","N","B","IY","IY","Z","AH","L","IY","IH","K","S","T","EH","N","D","AH","D","S","IH","N","S","IH","T","IH","Z","B","EY","S","T","AA","N","DH","AH","AH","B","JH","EH","K","T","M","AA","D","AH","L","."]	[{"g":"AA","i":1,"j":1,"p":"AW","op":"S"},{"g":"V","i":2,"j":2,"p":"ER","op":"S"},{"g":"AH","i":3,"j":3,"p":null,"op":"D"},{"g":"AH","i":39,"j":38,"p":"AA","op":"S"},{"g":".","i":50,"j":49,"p":null,"op":"D"}]	9.803921568627452	9.803921568627452	2025-09-14 16:09:57.992642+00
7	test123	2734c23205ea40dd6477d3587c18ebe82b593adb6dd7dae8c1fd62b9f0f3a9fe	In Java, everything is an object.	["IH","N","JH","AW","EH","V","R","AH","TH","IH","NG","IH","Z","AE","N","AA","B","JH","EH","K","T"]	["IH","N","JH","AA","V","AH",",","EH","V","R","IY","TH","IH","NG","IH","Z","AE","N","AH","B","JH","EH","K","T","."]	[{"g":"AA","i":3,"j":3,"p":"AW","op":"S"},{"g":"V","i":4,"j":4,"p":null,"op":"D"},{"g":"AH","i":5,"j":4,"p":null,"op":"D"},{"g":",","i":6,"j":4,"p":null,"op":"D"},{"g":"IY","i":10,"j":7,"p":"AH","op":"S"},{"g":"AH","i":18,"j":15,"p":"AA","op":"S"},{"g":".","i":24,"j":21,"p":null,"op":"D"}]	28	28	2025-09-14 16:11:06.17247+00
8	test123	775a5c6a1108ba11aef66b59435f013911e4939bafd8c60c202d2e22d1fc92f7	Java can be easily extended since it is based on the object model.	["JH","AW","ER","K","AE","N","B","IY","IY","Z","AH","L","IY","IH","K","S","T","EH","N","D","AH","D","S","IH","N","S","IH","T","IH","Z","B","EY","S","T","AA","N","DH","AH","AA","B","JH","EH","K","T","M","AA","D","AH","L"]	["JH","AA","V","AH","K","AE","N","B","IY","IY","Z","AH","L","IY","IH","K","S","T","EH","N","D","AH","D","S","IH","N","S","IH","T","IH","Z","B","EY","S","T","AA","N","DH","AH","AH","B","JH","EH","K","T","M","AA","D","AH","L","."]	[{"g":"AA","i":1,"j":1,"p":"AW","op":"S"},{"g":"V","i":2,"j":2,"p":"ER","op":"S"},{"g":"AH","i":3,"j":3,"p":null,"op":"D"},{"g":"AH","i":39,"j":38,"p":"AA","op":"S"},{"g":".","i":50,"j":49,"p":null,"op":"D"}]	9.803921568627452	9.803921568627452	2025-09-14 16:11:14.146423+00
9	test123	c0180510b2d43e66a6449ad81d529c69d2eac3bae36ff68ec6bcd71c41e93e1e	Unlike many other programming languages, when Java is compiled, it is not compiled into a platform-specific machine, rather into a platform-independent bytecode. This bytecode is distributed over the web and interpreted by the virtual machine on which platform it is being run on.	["AH","N","L","AY","K","M","EH","N","IY","AH","V","DH","ER","P","R","OW","G","R","AE","M","IH","NG","L","AE","NG","G","W","AH","JH","AH","Z","W","EH","N","JH","AE","AH","IH","Z","K","AH","M","P","AY","L","D","IH","T","IH","Z","N","AA","T","K","AH","M","P","AY","L","IH","N","T","UW","P","L","AE","T","F","AO","R","M","IH","S","P","AH","S","IH","F","IH","K","M","AH","SH","IY","N","R","AE","DH","ER","IH","N","T","UW","P","L","AE","T","F","AO","R","M","IH","N","D","AH","P","EH","N","D","AH","N","T","W","AY","T","K","OW","L","DH","IH","S","P","AY","T","K","AO","R","D","IH","Z","D","IH","S","T","R","AH","B","Y","UW","T","AH","D","AO","ER","W","EH","B","B","AH","N","IH","N","T","ER","P","R","AH","T","AH","D","B","AY","DH","AH","V","ER","CH","UW","AH","L","M","AH","SH","IY","N","AA","N","W","IH","CH","P","L","AE","T","F","AO","R","M","IH","T","IH","Z","B","IY","IH","NG","R","AH","N","N","OW","T"]	["AH","N","L","AY","K","M","EH","N","IY","AH","DH","ER","P","R","OW","G","R","AE","M","IH","NG","L","AE","NG","G","W","AH","JH","AH","Z",",","W","EH","N","JH","AA","V","AH","IH","Z","K","AH","M","P","AY","L","D",",","IH","T","IH","Z","N","AA","T","K","AH","M","P","AY","L","D","IH","N","T","UW","AH","P","L","AE","T","F","R","AH","M","S","IH","P","AH","N","S","IY","M","AH","SH","IY","N",",","R","AE","DH","ER","IH","N","T","UW","AH","P","L","AE","F","T","ER","D","AE","N","S","M","AH","N","T","B","AY","T","EH","K","T","OW","D",".","DH","IH","S","B","AY","T","EH","K","T","OW","D","IH","Z","D","IH","S","T","R","IH","B","Y","AH","T","AH","D","OW","V","ER","DH","AH","W","EH","B","AH","N","D","IH","N","T","ER","P","R","AH","T","AH","D","B","AY","DH","AH","V","ER","CH","UW","AH","L","M","AH","SH","IY","N","AA","N","W","IH","CH","P","L","AE","T","F","AO","R","M","IH","T","IH","Z","B","IY","IH","NG","R","AH","N","AA","N","."]	[{"g":null,"i":10,"j":10,"p":"V","op":"I"},{"g":",","i":30,"j":31,"p":null,"op":"D"},{"g":"AA","i":35,"j":35,"p":"AE","op":"S"},{"g":"V","i":36,"j":36,"p":null,"op":"D"},{"g":",","i":47,"j":46,"p":null,"op":"D"},{"g":"D","i":61,"j":59,"p":null,"op":"D"},{"g":"AH","i":66,"j":63,"p":null,"op":"D"},{"g":null,"i":72,"j":68,"p":"AO","op":"I"},{"g":"AH","i":73,"j":70,"p":"M","op":"S"},{"g":"M","i":74,"j":71,"p":"IH","op":"S"},{"g":"IH","i":76,"j":73,"p":null,"op":"D"},{"g":null,"i":79,"j":75,"p":"S","op":"I"},{"g":null,"i":79,"j":76,"p":"IH","op":"I"},{"g":"N","i":79,"j":77,"p":"F","op":"S"},{"g":"S","i":80,"j":78,"p":"IH","op":"S"},{"g":"IY","i":81,"j":79,"p":"K","op":"S"},{"g":",","i":87,"j":85,"p":null,"op":"D"},{"g":"AH","i":96,"j":93,"p":null,"op":"D"},{"g":null,"i":100,"j":96,"p":"T","op":"I"},{"g":null,"i":101,"j":98,"p":"AO","op":"I"},{"g":null,"i":101,"j":99,"p":"R","op":"I"},{"g":null,"i":101,"j":100,"p":"M","op":"I"},{"g":"T","i":101,"j":101,"p":"IH","op":"S"},{"g":"ER","i":102,"j":102,"p":"N","op":"S"},{"g":null,"i":104,"j":104,"p":"AH","op":"I"},{"g":null,"i":104,"j":105,"p":"P","op":"I"},{"g":"AE","i":104,"j":106,"p":"EH","op":"S"},{"g":"S","i":106,"j":108,"p":"D","op":"S"},{"g":"M","i":107,"j":109,"p":null,"op":"D"},{"g":"B","i":111,"j":112,"p":"W","op":"S"},{"g":"EH","i":114,"j":115,"p":null,"op":"D"},{"g":"T","i":116,"j":116,"p":null,"op":"D"},{"g":"D","i":118,"j":117,"p":"L","op":"S"},{"g":".","i":119,"j":118,"p":null,"op":"D"},{"g":"B","i":123,"j":121,"p":"P","op":"S"},{"g":"EH","i":126,"j":124,"p":null,"op":"D"},{"g":"T","i":128,"j":125,"p":"AO","op":"S"},{"g":"OW","i":129,"j":126,"p":"R","op":"S"},{"g":"IH","i":138,"j":135,"p":"AH","op":"S"},{"g":"AH","i":141,"j":138,"p":"UW","op":"S"},{"g":"OW","i":145,"j":142,"p":"AO","op":"S"},{"g":"V","i":146,"j":143,"p":null,"op":"D"},{"g":"DH","i":148,"j":144,"p":null,"op":"D"},{"g":"AH","i":149,"j":144,"p":null,"op":"D"},{"g":null,"i":153,"j":147,"p":"B","op":"I"},{"g":"D","i":155,"j":150,"p":null,"op":"D"},{"g":"AA","i":205,"j":199,"p":"N","op":"S"},{"g":"N","i":206,"j":200,"p":"OW","op":"S"},{"g":".","i":207,"j":201,"p":"T","op":"S"}]	23.557692307692307	23.557692307692307	2025-09-14 16:11:36.696478+00
10	test123	ee71fc5417eae9ee2fcc1e3f9c8fcb1169ac6352867db12c45a82a054e973acb	Java is designed to be easy to learn. If you understand the basic concept of OOP, Java, it would be easy to master.	["JH","AE","AH","IH","Z","D","IH","Z","AY","N","D","T","UW","B","IY","IY","Z","IY","T","UW","L","ER","N","IH","F","Y","UW","AH","N","D","ER","S","T","AE","N","D","DH","AH","B","EY","S","IH","K","K","AH","N","S","EH","P","T","AH","V","AO","OW","K","IY","JH","AE","V","AH","IH","K","W","UH","D","B","IY","IY","Z","AH","L","UW","M","AE","S","T","ER"]	["JH","AA","V","AH","IH","Z","D","IH","Z","AY","N","D","T","UW","B","IY","IY","Z","IY","T","UW","L","ER","N",".","IH","F","Y","UW","AH","N","D","ER","S","T","AE","N","D","DH","AH","B","EY","S","IH","K","K","AA","N","S","EH","P","T","AH","V","UW","P",",","JH","AA","V","AH",",","IH","T","W","UH","D","B","IY","IY","Z","IY","T","UW","M","AE","S","T","ER","."]	[{"g":"AA","i":1,"j":1,"p":"AE","op":"S"},{"g":"V","i":2,"j":2,"p":null,"op":"D"},{"g":".","i":24,"j":23,"p":null,"op":"D"},{"g":"AA","i":46,"j":44,"p":"AH","op":"S"},{"g":null,"i":54,"j":52,"p":"AO","op":"I"},{"g":"UW","i":54,"j":53,"p":"OW","op":"S"},{"g":"P","i":55,"j":54,"p":"K","op":"S"},{"g":",","i":56,"j":55,"p":"IY","op":"S"},{"g":"AA","i":58,"j":57,"p":"AE","op":"S"},{"g":",","i":61,"j":60,"p":null,"op":"D"},{"g":"T","i":63,"j":61,"p":"K","op":"S"},{"g":"IY","i":71,"j":69,"p":"AH","op":"S"},{"g":"T","i":72,"j":70,"p":"L","op":"S"},{"g":".","i":79,"j":77,"p":null,"op":"D"}]	17.5	17.5	2025-09-14 16:11:45.915895+00
11	test123	37f39bcda59bacb2c3295fffcbb64bd8c6f9e438842d4c91a8eef8bfa8051e45	cho vá»›i cÃ´ng váº¥n Generates and Architecture New Tools á»•n chá»©c pháº£i phÃ´ máº¡t.	["HH","AH","K","AH","M","P","AY","L","AH","JH","EH","N","ER","EY","T","S","AH","N","AA","R","HH","AH","T","EH","K","CH","ER","N","UW","T","R","AH","L","AA","B","JH","IH","K","T","F","AY","L","F","AO","R","M","AH","N"]	["CH","OW","V","OY","K","AO","NG","V","AE","N","JH","EH","N","ER","EY","T","S","AH","N","D","AA","R","K","AH","T","EH","K","CH","ER","N","UW","T","UW","L","Z","AA","N","CH","AH","K","F","EY","F","OW","M","AE","T","."]	[{"g":"CH","i":0,"j":0,"p":"HH","op":"S"},{"g":"OW","i":1,"j":1,"p":"AH","op":"S"},{"g":"V","i":2,"j":2,"p":"K","op":"S"},{"g":"OY","i":3,"j":3,"p":"AH","op":"S"},{"g":"K","i":4,"j":4,"p":"M","op":"S"},{"g":"AO","i":5,"j":5,"p":"P","op":"S"},{"g":"NG","i":6,"j":6,"p":"AY","op":"S"},{"g":"V","i":7,"j":7,"p":"L","op":"S"},{"g":"AE","i":8,"j":8,"p":"AH","op":"S"},{"g":"N","i":9,"j":9,"p":null,"op":"D"},{"g":"D","i":19,"j":18,"p":null,"op":"D"},{"g":"K","i":22,"j":20,"p":"HH","op":"S"},{"g":null,"i":32,"j":30,"p":"R","op":"I"},{"g":"UW","i":32,"j":31,"p":"AH","op":"S"},{"g":"Z","i":34,"j":33,"p":null,"op":"D"},{"g":"N","i":36,"j":34,"p":"B","op":"S"},{"g":"CH","i":37,"j":35,"p":"JH","op":"S"},{"g":"AH","i":38,"j":36,"p":"IH","op":"S"},{"g":null,"i":40,"j":38,"p":"T","op":"I"},{"g":null,"i":41,"j":40,"p":"AY","op":"I"},{"g":"EY","i":41,"j":41,"p":"L","op":"S"},{"g":null,"i":43,"j":43,"p":"AO","op":"I"},{"g":"OW","i":43,"j":44,"p":"R","op":"S"},{"g":"AE","i":45,"j":46,"p":"AH","op":"S"},{"g":"T","i":46,"j":47,"p":"N","op":"S"},{"g":".","i":47,"j":48,"p":null,"op":"D"}]	54.166666666666664	54.166666666666664	2025-09-14 16:11:57.834405+00
12	test123	7832131fdeb16cc1443a1979fc513b47933f173c1dbfa97fe892b50f37f56c80	which makes the compiled code executable on many processors.	["W","IH","CH","M","EY","K","S","DH","AH","K","AH","M","P","AY","N","K","AO","R","T","D","IH","G","S","EH","K","Y","UW","T","AH","B","AH","L","AA","N","M","EH","N","IY","P","AA","S","EH","S","ER","Z"]	["W","IH","CH","M","EY","K","S","DH","AH","K","AH","M","P","AY","L","D","K","OW","D","EH","K","S","AH","K","Y","UW","T","AH","B","AH","L","AA","N","M","EH","N","IY","P","R","AA","S","EH","S","ER","Z","."]	[{"g":null,"i":14,"j":14,"p":"N","op":"I"},{"g":"L","i":14,"j":15,"p":"K","op":"S"},{"g":"D","i":15,"j":16,"p":"AO","op":"S"},{"g":"K","i":16,"j":17,"p":"R","op":"S"},{"g":"OW","i":17,"j":18,"p":"T","op":"S"},{"g":"EH","i":19,"j":20,"p":"IH","op":"S"},{"g":"K","i":20,"j":21,"p":"G","op":"S"},{"g":"AH","i":22,"j":23,"p":"EH","op":"S"},{"g":"R","i":38,"j":39,"p":null,"op":"D"},{"g":".","i":45,"j":45,"p":null,"op":"D"}]	21.73913043478261	21.73913043478261	2025-09-14 16:12:05.100715+00
13	test123	5a064d793580b8eebe688ac4f5cea61611c4fc1d57e77d8c000e0eb2189cf7e8	Being architecture-neutral and having no implementation-dependent aspect of the specification makes Java portable. Compiler in Java is written in C.	["B","IY","IH","NG","AA","R","K","AH","T","EH","K","CH","ER","N","UW","T","R","AH","L","AH","N","D","HH","AE","V","IH","NG","N","OW","IH","M","P","L","AH","M","AH","N","T","EY","SH","AH","N","D","IH","P","EH","N","D","AH","N","T","AE","S","P","EH","K","T","AH","V","DH","AH","IH","S","P","EH","CH","IY","EY","SH","AH","N","M","EY","K","S","JH","AW","AH","P","AO","R","T","AH","B","AH","L","K","AH","M","P","AY","L","ER","IH","N","JH","AW","AH","IY","S","T","R","IH","DH","AH","M","IH","N","S","IY"]	["B","IY","IH","NG","AA","R","K","AH","T","EH","K","SH","AH","N","T","R","AH","T","AH","N","D","HH","AE","V","IH","NG","N","OW","IH","M","P","L","AH","D","M","EH","P","T","AH","N","SH","AH","N","T","AE","S","P","EH","K","T","AH","V","DH","AH","S","P","EH","S","IH","F","IH","K","EY","SH","AH","N","M","EY","K","S","JH","AA","V","AH","P","AO","R","T","AH","B","AH","L",".","K","AH","M","P","AY","L","ER","IH","N","JH","AA","V","AH","IH","Z","R","IH","T","AH","N","IH","N","S","IY","."]	[{"g":"SH","i":11,"j":11,"p":"CH","op":"S"},{"g":"AH","i":12,"j":12,"p":"ER","op":"S"},{"g":null,"i":14,"j":14,"p":"UW","op":"I"},{"g":"T","i":17,"j":18,"p":"L","op":"S"},{"g":"D","i":33,"j":34,"p":null,"op":"D"},{"g":"EH","i":35,"j":35,"p":"AH","op":"S"},{"g":"P","i":36,"j":36,"p":"N","op":"S"},{"g":null,"i":38,"j":38,"p":"EY","op":"I"},{"g":null,"i":38,"j":39,"p":"SH","op":"I"},{"g":null,"i":40,"j":42,"p":"D","op":"I"},{"g":null,"i":40,"j":43,"p":"IH","op":"I"},{"g":null,"i":40,"j":44,"p":"P","op":"I"},{"g":null,"i":40,"j":45,"p":"EH","op":"I"},{"g":null,"i":40,"j":46,"p":"N","op":"I"},{"g":"SH","i":40,"j":47,"p":"D","op":"S"},{"g":null,"i":54,"j":61,"p":"IH","op":"I"},{"g":"S","i":57,"j":65,"p":"CH","op":"S"},{"g":"IH","i":58,"j":66,"p":"IY","op":"S"},{"g":"F","i":59,"j":67,"p":null,"op":"D"},{"g":"IH","i":60,"j":67,"p":null,"op":"D"},{"g":"K","i":61,"j":67,"p":null,"op":"D"},{"g":"AA","i":71,"j":76,"p":"AW","op":"S"},{"g":"V","i":72,"j":77,"p":null,"op":"D"},{"g":".","i":82,"j":86,"p":null,"op":"D"},{"g":"AA","i":93,"j":96,"p":"AW","op":"S"},{"g":"V","i":94,"j":97,"p":"AH","op":"S"},{"g":"AH","i":95,"j":98,"p":"IY","op":"S"},{"g":"IH","i":96,"j":99,"p":"S","op":"S"},{"g":"Z","i":97,"j":100,"p":"T","op":"S"},{"g":"T","i":100,"j":103,"p":"DH","op":"S"},{"g":"N","i":102,"j":105,"p":"M","op":"S"},{"g":".","i":107,"j":110,"p":null,"op":"D"}]	29.62962962962963	29.62962962962963	2025-09-14 16:12:18.646095+00
18	test123	eb3074195ae162a82257268ae4e207a9bcabcd59a6613c7ac4c4c626bbffb888	The development process is more rapid and analytical since the linking is an incremental and lightweight process.	["DH","AH","D","IH","V","ER","AH","P","M","AH","N","T","P","AH","Z","EH","S","IH","Z","M","AO","R","R","AE","P","IH","D","AH","N","D","AE","N","AH","L","IH","T","IH","K","AH","L","S","IH","N","S","DH","AH","L","IH","NG","K","IH","NG","IY","S","AH","N","IH","N","K","R","AH","M","EH","N","T","AH","L","AH","N","D","L","AY","T","W","EY","P","AH","Z","EH","S"]	["DH","AH","D","IH","V","EH","L","AH","P","M","AH","N","T","P","R","AA","S","EH","S","IH","Z","M","AO","R","R","AE","P","AH","D","AH","N","D","AE","N","AH","L","IH","T","IH","K","AH","L","S","IH","N","S","DH","AH","L","IH","NG","K","IH","NG","IH","Z","AE","N","IH","N","K","R","AH","M","EH","N","T","AH","L","AH","N","D","L","AY","T","W","EY","T","P","R","AA","S","EH","S","."]	[{"g":"EH","i":5,"j":5,"p":"ER","op":"S"},{"g":"L","i":6,"j":6,"p":null,"op":"D"},{"g":"R","i":14,"j":13,"p":"AH","op":"S"},{"g":"AA","i":15,"j":14,"p":"Z","op":"S"},{"g":"S","i":16,"j":15,"p":null,"op":"D"},{"g":"AH","i":27,"j":25,"p":"IH","op":"S"},{"g":"IH","i":54,"j":52,"p":"IY","op":"S"},{"g":"Z","i":55,"j":53,"p":"S","op":"S"},{"g":"AE","i":56,"j":54,"p":"AH","op":"S"},{"g":"T","i":77,"j":75,"p":null,"op":"D"},{"g":"R","i":79,"j":76,"p":"AH","op":"S"},{"g":"AA","i":80,"j":77,"p":"Z","op":"S"},{"g":"S","i":81,"j":78,"p":null,"op":"D"},{"g":".","i":84,"j":80,"p":null,"op":"D"}]	16.470588235294116	16.470588235294116	2025-09-14 16:13:17.005786+00
14	test123	909ada4b4da8b5fbf69103e21ab4988459308b0b5483f4f00f806f83ceca385b	Just to give you a little excitement about java programming, I am going to give you a small convenient C programming hello world program. You can try it using demo link.	["JH","AH","S","T","UW","G","IH","V","Y","UW","AH","L","IH","T","AH","L","IH","K","S","AY","T","M","AH","N","T","AH","B","AW","T","D","AW","AH","P","R","OW","G","AE","N","M","IH","NG","AY","AE","M","G","OW","IH","N","T","UW","G","IH","V","V","Y","UW","AH","AH","S","M","AO","L","K","AH","N","V","IY","N","Y","AH","N","T","S","IY","P","R","OW","G","R","AE","M","IH","NG","HH","EH","L","OW","W","ER","L","D","P","R","OW","G","R","AE","M","Y","UW","K","AE","N","T","R","AY","IH","T","Y","UW","Z","IH","NG","DH","AH","M","AA","L","IH","NG","K"]	["JH","AH","S","T","T","UW","G","IH","V","Y","UW","AH","L","IH","T","AH","L","IH","K","S","AY","T","M","AH","N","T","AH","B","AW","T","JH","AA","V","AH","P","R","OW","G","R","AE","M","IH","NG",",","AY","AE","M","G","OW","IH","NG","T","UW","G","IH","V","Y","UW","AH","S","M","AO","L","K","AH","N","V","IY","N","Y","AH","N","T","S","IY","P","R","OW","G","R","AE","M","IH","NG","HH","AH","L","OW","W","ER","L","D","P","R","OW","G","R","AE","M",".","Y","UW","K","AE","N","T","R","AY","IH","T","Y","UW","Z","IH","NG","D","EH","M","OW","L","IH","NG","K","."]	[{"g":"T","i":4,"j":4,"p":null,"op":"D"},{"g":"JH","i":30,"j":29,"p":"D","op":"S"},{"g":"AA","i":31,"j":30,"p":"AW","op":"S"},{"g":"V","i":32,"j":31,"p":null,"op":"D"},{"g":"R","i":38,"j":36,"p":"AE","op":"S"},{"g":"AE","i":39,"j":37,"p":"N","op":"S"},{"g":",","i":43,"j":41,"p":null,"op":"D"},{"g":"NG","i":50,"j":47,"p":"N","op":"S"},{"g":null,"i":56,"j":53,"p":"V","op":"I"},{"g":null,"i":59,"j":57,"p":"AH","op":"I"},{"g":"AH","i":85,"j":84,"p":"EH","op":"S"},{"g":".","i":99,"j":98,"p":null,"op":"D"},{"g":"D","i":115,"j":113,"p":"DH","op":"S"},{"g":"EH","i":116,"j":114,"p":"AH","op":"S"},{"g":"OW","i":118,"j":116,"p":"AA","op":"S"},{"g":".","i":123,"j":121,"p":null,"op":"D"}]	12.903225806451612	12.903225806451612	2025-09-14 16:12:31.517963+00
15	test123	fb51f47ae871356e2cb0154cdeadc3c34c22a3e5f2eefa5791489925605aea9d	The latest release of the Java Standard Edition is 8. With the advancement of Java and its widespread popularity, multiple configurations were built to suit various types of platforms.	["DH","AH","L","EY","T","ER","Z","R","IY","L","IY","S","AH","V","DH","AH","JH","AW","AH","IH","S","T","AE","N","D","ER","D","AH","D","IH","ZH","AH","N","IY","Z","EY","T","W","IH","DH","DH","AH","AE","D","V","AY","Z","M","AH","N","T","AH","V","DH","AH","JH","AW","AH","AH","N","D","IH","T","S","W","AY","D","S","P","R","EH","D","P","AA","P","Y","AH","L","EH","R","AH","T","IY","M","AH","L","T","AH","P","AH","L","K","AH","N","T","F","IH","G","ER","EY","JH","AH","N","Z","W","ER","B","IH","L","T","UW","S","UH","R","TH","V","EH","R","IY","AH","S","T","AY","P","AH","V","P","L","AE","T","F","AO","R","M","Z"]	["DH","AH","L","EY","T","AH","S","T","R","IY","L","IY","S","AH","V","DH","AH","JH","AA","V","AH","S","T","AE","N","D","ER","D","AH","D","IH","SH","AH","N","IH","Z","EY","T",".","W","IH","DH","DH","AH","AH","D","V","AE","N","S","M","AH","N","T","AH","V","JH","AA","V","AH","AH","N","D","IH","T","S","W","AY","D","S","P","R","EH","D","P","AA","P","Y","AH","L","EH","R","AH","T","IY",",","M","AH","L","T","AH","P","AH","L","K","AH","N","F","IH","G","Y","ER","EY","SH","AH","N","Z","W","ER","B","IH","L","T","T","UW","S","UW","T","V","EH","R","IY","AH","S","T","AY","P","S","AH","V","P","L","AE","T","F","AO","R","M","Z","."]	[{"g":"AH","i":5,"j":5,"p":"ER","op":"S"},{"g":"S","i":6,"j":6,"p":"Z","op":"S"},{"g":"T","i":7,"j":7,"p":null,"op":"D"},{"g":"AA","i":18,"j":17,"p":"AW","op":"S"},{"g":"V","i":19,"j":18,"p":"AH","op":"S"},{"g":"AH","i":20,"j":19,"p":"IH","op":"S"},{"g":"SH","i":31,"j":30,"p":"ZH","op":"S"},{"g":"IH","i":34,"j":33,"p":"IY","op":"S"},{"g":".","i":38,"j":37,"p":null,"op":"D"},{"g":"AH","i":44,"j":42,"p":"AE","op":"S"},{"g":"AE","i":47,"j":45,"p":"AY","op":"S"},{"g":"N","i":48,"j":46,"p":"Z","op":"S"},{"g":"S","i":49,"j":47,"p":null,"op":"D"},{"g":null,"i":56,"j":53,"p":"DH","op":"I"},{"g":null,"i":56,"j":54,"p":"AH","op":"I"},{"g":"AA","i":57,"j":56,"p":"AW","op":"S"},{"g":"V","i":58,"j":57,"p":null,"op":"D"},{"g":",","i":85,"j":83,"p":null,"op":"D"},{"g":null,"i":97,"j":94,"p":"T","op":"I"},{"g":"Y","i":100,"j":98,"p":null,"op":"D"},{"g":"SH","i":103,"j":100,"p":"JH","op":"S"},{"g":"T","i":113,"j":110,"p":null,"op":"D"},{"g":null,"i":116,"j":112,"p":"UH","op":"I"},{"g":"UW","i":116,"j":113,"p":"R","op":"S"},{"g":"T","i":117,"j":114,"p":"TH","op":"S"},{"g":"S","i":127,"j":124,"p":null,"op":"D"},{"g":".","i":139,"j":135,"p":null,"op":"D"}]	19.285714285714285	19.285714285714285	2025-09-14 16:12:51.389277+00
16	test123	30b123699df32b95210ab88976125d2194e25f3094148d6be1713d0b6c8d757f	This design feature allows the developers to construct interactive applications that can run smoothly.	["DH","IH","S","D","IH","Z","AY","N","F","IY","CH","ER","AE","R","AO","L","S","OW","AH","D","UH","R","AH","P","S","T","UW","K","AH","N","S","T","R","AH","K","T","IH","N","T","ER","AE","K","T","IH","V","AE","P","L","AH","K","EY","SH","AH","N","DH","AE","T","K","AE","N","T","R","AH","N","IH","Z","M","OW","T","L","IY"]	["DH","IH","S","D","IH","Z","AY","N","F","IY","CH","ER","AH","L","AW","Z","DH","AH","D","IH","V","EH","L","AH","P","ER","Z","T","UW","K","AH","N","S","T","R","AH","K","T","IH","N","T","ER","AE","K","T","IH","V","AE","P","L","AH","K","EY","SH","AH","N","Z","DH","AE","T","K","AE","N","R","AH","N","S","M","UW","DH","L","IY","."]	[{"g":null,"i":12,"j":12,"p":"AE","op":"I"},{"g":null,"i":12,"j":13,"p":"R","op":"I"},{"g":"AH","i":12,"j":14,"p":"AO","op":"S"},{"g":"AW","i":14,"j":16,"p":"S","op":"S"},{"g":"Z","i":15,"j":17,"p":"OW","op":"S"},{"g":"DH","i":16,"j":18,"p":null,"op":"D"},{"g":"IH","i":19,"j":20,"p":"UH","op":"S"},{"g":"V","i":20,"j":21,"p":"R","op":"S"},{"g":"EH","i":21,"j":22,"p":null,"op":"D"},{"g":"L","i":22,"j":22,"p":null,"op":"D"},{"g":"ER","i":25,"j":24,"p":"S","op":"S"},{"g":"Z","i":26,"j":25,"p":null,"op":"D"},{"g":"Z","i":56,"j":54,"p":null,"op":"D"},{"g":null,"i":63,"j":60,"p":"T","op":"I"},{"g":null,"i":66,"j":64,"p":"IH","op":"I"},{"g":"S","i":66,"j":65,"p":"Z","op":"S"},{"g":"UW","i":68,"j":67,"p":"OW","op":"S"},{"g":"DH","i":69,"j":68,"p":"T","op":"S"},{"g":".","i":72,"j":71,"p":null,"op":"D"}]	26.027397260273972	26.027397260273972	2025-09-14 16:13:00.112267+00
17	test123	1b92c66d378536600f94368eb73e8ecc2bb3469b8f43332329712c231016d565	Java bytecode is translated on the fly to native machine instruction and is not stored anywhere.	["JH","AW","AH","B","AY","T","K","OW","D","IH","Z","T","R","AE","N","S","L","EY","T","AH","AA","N","DH","AH","F","L","AY","T","UW","N","EY","T","IH","V","M","AH","SH","IY","N","IH","N","S","T","R","AH","K","SH","AH","N","AH","N","D","IY","S","N","OW","T","S","T","OW","T","EH","N","IY","M","EH","R"]	["JH","AA","V","AH","B","AY","T","EH","K","T","OW","D","IH","Z","T","R","AE","N","Z","L","EY","T","AH","D","AA","N","DH","AH","F","L","AY","T","UW","N","EY","T","IH","V","M","AH","SH","IY","N","IH","N","S","T","R","AH","K","SH","AH","N","AH","N","D","IH","Z","N","AA","T","S","T","AO","R","D","EH","N","IY","W","EH","R","."]	[{"g":"AA","i":1,"j":1,"p":"AW","op":"S"},{"g":"V","i":2,"j":2,"p":null,"op":"D"},{"g":"EH","i":7,"j":6,"p":null,"op":"D"},{"g":"T","i":9,"j":7,"p":null,"op":"D"},{"g":"Z","i":18,"j":15,"p":"S","op":"S"},{"g":"D","i":23,"j":20,"p":null,"op":"D"},{"g":"IH","i":56,"j":52,"p":"IY","op":"S"},{"g":"Z","i":57,"j":53,"p":"S","op":"S"},{"g":"AA","i":59,"j":55,"p":"OW","op":"S"},{"g":"AO","i":63,"j":59,"p":"OW","op":"S"},{"g":"R","i":64,"j":60,"p":"T","op":"S"},{"g":"D","i":65,"j":61,"p":null,"op":"D"},{"g":"W","i":69,"j":64,"p":"M","op":"S"},{"g":".","i":72,"j":67,"p":null,"op":"D"}]	19.17808219178082	19.17808219178082	2025-09-14 16:13:09.708413+00
19	test123	93cdcea3c270ce09251a6352fe1a6be614b75cc39f2db6b1c958a06c7a0625fe	With the use of just in-time compilers, Java enables high performance.	["W","IH","D","DH","AH","Y","UW","S","AH","V","JH","AH","S","T","IH","N","T","AY","M","K","AH","M","P","AY","L","ER","Z","JH","AW","AH","EH","N","EY","B","AH","L","Z","HH","AY","P","ER","F","AO","R","M","AH","N","S"]	["W","IH","DH","DH","AH","Y","UW","S","AH","V","JH","AH","S","T","IH","N","T","AY","M","K","AH","M","P","AY","L","ER","Z",",","JH","AA","V","AH","EH","N","EY","B","AH","L","Z","HH","AY","P","ER","F","AO","R","M","AH","N","S","."]	[{"g":"DH","i":2,"j":2,"p":"D","op":"S"},{"g":",","i":27,"j":27,"p":null,"op":"D"},{"g":"AA","i":29,"j":28,"p":"AW","op":"S"},{"g":"V","i":30,"j":29,"p":null,"op":"D"},{"g":".","i":50,"j":48,"p":null,"op":"D"}]	9.803921568627452	9.803921568627452	2025-09-14 16:13:23.005111+00
20	test123	d66e63c04573c0faa4a49648d7d17220bda037977b32749731b0dd71245dc0c7	Java is considered to be a more dynamic programming language.	["K","AE","AH","IH","Z","K","AH","N","S","IH","D","ER","D","T","UW","B","IY","AH","M","OW","D","AY","IH","N","AH","M","IH","P","R","OW","G","AE","M","IH","L","AE","NG","G","W","IY","JH"]	["JH","AA","V","AH","IH","Z","K","AH","N","S","IH","D","ER","D","T","UW","B","IY","AH","M","AO","R","D","AY","N","AE","M","IH","K","P","R","OW","G","R","AE","M","IH","NG","L","AE","NG","G","W","AH","JH","."]	[{"g":"JH","i":0,"j":0,"p":"K","op":"S"},{"g":"AA","i":1,"j":1,"p":"AE","op":"S"},{"g":"V","i":2,"j":2,"p":null,"op":"D"},{"g":"AO","i":20,"j":19,"p":"OW","op":"S"},{"g":"R","i":21,"j":20,"p":null,"op":"D"},{"g":null,"i":24,"j":22,"p":"IH","op":"I"},{"g":"AE","i":25,"j":24,"p":"AH","op":"S"},{"g":"K","i":28,"j":27,"p":null,"op":"D"},{"g":"R","i":33,"j":31,"p":null,"op":"D"},{"g":"NG","i":37,"j":34,"p":null,"op":"D"},{"g":"AH","i":43,"j":39,"p":"IY","op":"S"},{"g":".","i":45,"j":41,"p":null,"op":"D"}]	26.08695652173913	26.08695652173913	2025-09-14 16:13:28.540615+00
21	test123	7ea15b891ae7f0154a35998182b444f075f1ab48c6f5135fe3c55615656bdf48	Java programs can carry extensive amount of runtime information that can be used to verify and resolve access to objects on runtime.	["JH","AW","ER","P","R","OW","G","R","AE","M","Z","K","AE","N","K","AE","R","IY","IH","K","S","T","EH","N","S","IH","V","AH","M","AH","N","T","AH","V","F","R","AH","N","T","AY","M","IH","N","F","ER","M","EY","SH","AH","N","DH","AE","T","K","AE","N","B","IY","Y","UW","Z","D","T","UW","V","EH","R","AH","F","AY","AH","N","D","R","IH","Z","AA","V","AE","K","S","EH","S","T","UW","AH","V","B","JH","AH","T","AA","N","T","R","AH","N","T","AY","M"]	["JH","AA","V","AH","P","R","OW","G","R","AE","M","Z","K","AE","N","K","AE","R","IY","IH","K","S","T","EH","N","S","IH","V","AH","M","AW","N","T","AH","V","R","AH","N","T","AY","M","IH","N","F","ER","M","EY","SH","AH","N","DH","AE","T","K","AE","N","B","IY","Y","UW","Z","D","T","UW","V","EH","R","AH","F","AY","AH","N","D","R","IY","Z","AA","L","V","AE","K","S","EH","S","T","UW","AA","B","JH","EH","K","T","S","AA","N","R","AH","N","T","AY","M","."]	[{"g":"AA","i":1,"j":1,"p":"AW","op":"S"},{"g":"V","i":2,"j":2,"p":"ER","op":"S"},{"g":"AH","i":3,"j":3,"p":null,"op":"D"},{"g":"AW","i":30,"j":29,"p":"AH","op":"S"},{"g":null,"i":35,"j":34,"p":"F","op":"I"},{"g":"IY","i":74,"j":74,"p":"IH","op":"S"},{"g":"L","i":77,"j":77,"p":null,"op":"D"},{"g":null,"i":86,"j":85,"p":"AH","op":"I"},{"g":"AA","i":86,"j":86,"p":"V","op":"S"},{"g":"EH","i":89,"j":89,"p":"AH","op":"S"},{"g":"K","i":90,"j":90,"p":null,"op":"D"},{"g":"S","i":92,"j":91,"p":null,"op":"D"},{"g":null,"i":95,"j":93,"p":"T","op":"I"},{"g":".","i":101,"j":100,"p":null,"op":"D"}]	13.72549019607843	13.72549019607843	2025-09-14 16:13:40.483539+00
