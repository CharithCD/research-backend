
from . import db
from .analytics import compute_last7d

async def recompute_all_users_analytics():
    # This is a placeholder. In a real app, you'd get a list of active users.
    # For now, we'll just recompute for users we have recent results for.
    print("Starting daily analytics recomputation...")
    user_ids = set()
    
    # A more efficient way would be a single query to get distinct user IDs
    # but this is fine for a small number of users.
    phoneme_results = await db.get_phoneme_results_last_n_days(user_id="%", days=7) # Wildcard might not work, depends on DB
    grammar_results = await db.get_grammar_results_last_n_days(user_id="%", days=7)

    for r in phoneme_results:
        user_ids.add(r.user_id)
    for r in grammar_results:
        user_ids.add(r.user_id)

    print(f"Found {len(user_ids)} active users to recompute analytics for.")
    for user_id in user_ids:
        try:
            analytics_data = await compute_last7d(user_id)
            await db.upsert_user_analytics_cache(analytics_data)
            print(f"Successfully recomputed analytics for user: {user_id}")
        except Exception as e:
            print(f"[ERROR] Failed to recompute analytics for user {user_id}: {e}")
    print("Daily analytics recomputation finished.")
