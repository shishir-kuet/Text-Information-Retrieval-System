from backend.app.config.database import get_database
from backend.app.models import ensure_schema_indexes, now_str


def _next_log_id(db):
    last = db['search_logs'].find_one(sort=[('log_id', -1)])
    if not last or 'log_id' not in last:
        return 1
    return int(last['log_id']) + 1


def create_search_log(*, user_id, query_text, normalized_query, total_results, top_results, latency_ms):
    ensure_schema_indexes()
    db = get_database()
    log_doc = {
        'log_id': _next_log_id(db),
        'user_id': user_id,
        'query_text': query_text,
        'normalized_query': normalized_query,
        'total_results': total_results,
        'top_results': top_results,
        'latency_ms': latency_ms,
        'created_at': now_str(),
    }
    db['search_logs'].insert_one(log_doc)
    return log_doc


def get_user_history(user_id: int, limit: int = 50):
    ensure_schema_indexes()
    db = get_database()
    cursor = db['search_logs'].find({'user_id': user_id}).sort('created_at', -1).limit(limit)
    return list(cursor)


def delete_user_history_item(user_id: int, log_id: int):
    ensure_schema_indexes()
    db = get_database()
    res = db['search_logs'].delete_one({'user_id': user_id, 'log_id': log_id})
    return res.deleted_count


def clear_user_history(user_id: int):
    ensure_schema_indexes()
    db = get_database()
    res = db['search_logs'].delete_many({'user_id': user_id})
    return res.deleted_count


def get_admin_search_logs(limit: int = 100, skip: int = 0):
    ensure_schema_indexes()
    db = get_database()
    cursor = db['search_logs'].find({}).sort('created_at', -1).skip(skip).limit(limit)
    return list(cursor)


