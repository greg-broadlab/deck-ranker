import os
import threading
from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for
from config import PORT, CATEGORIES
from database import (init_db, get_decks_by_category, get_comparison_pair,
                      record_vote, get_deck, mark_rendered, get_category_stats)
from scanner import scan
from elo import update
from renderer import render_deck, is_rendered, get_slide_path, get_slide_count, get_cache_dir

app = Flask(__name__)

rendering_status = {}
rendering_lock = threading.Lock()


def render_in_background(deck_id, pptx_path):
    try:
        slide_count = render_deck(deck_id, pptx_path)
        mark_rendered(deck_id, slide_count)
        with rendering_lock:
            rendering_status[deck_id] = 'done'
    except Exception as e:
        with rendering_lock:
            rendering_status[deck_id] = 'error'
        print(f"Render error for {deck_id}: {e}")


def ensure_rendering(deck):
    did = deck['id']
    if is_rendered(did):
        with rendering_lock:
            rendering_status[did] = 'done'
        return
    with rendering_lock:
        if did not in rendering_status or rendering_status[did] == 'error':
            rendering_status[did] = 'rendering'
            t = threading.Thread(target=render_in_background, args=(did, deck['path']), daemon=True)
            t.start()


@app.route('/')
def index():
    stats = {}
    for cat_id, cat_name in CATEGORIES.items():
        decks = get_decks_by_category(cat_id)
        total, matches = get_category_stats(cat_id)
        stats[cat_id] = {
            'name': cat_name,
            'count': total,
            'matches': matches,
            'top': decks[:5],
        }
    return render_template('index.html', categories=stats)


@app.route('/compare/<category>')
def compare(category):
    if category not in CATEGORIES:
        abort(404)

    deck_a, deck_b = get_comparison_pair(category)
    if not deck_a or not deck_b:
        return render_template('no_decks.html', category_name=CATEGORIES[category], category=category)

    ensure_rendering(deck_a)
    ensure_rendering(deck_b)

    return render_template('compare.html',
                           category=category,
                           category_name=CATEGORIES[category],
                           deck_a=deck_a,
                           deck_b=deck_b,
                           all_categories=CATEGORIES)


@app.route('/api/render-status/<deck_id>')
def render_status(deck_id):
    slides_done = get_slide_count(deck_id)
    with rendering_lock:
        status = rendering_status.get(deck_id, 'unknown')
    # Trust the file system — if slides exist, it's done regardless of memory state
    if slides_done > 0 and status != 'error':
        status = 'done'
    deck = get_deck(deck_id)
    total = deck['slide_count'] if deck and deck['slide_count'] > 0 else None
    return jsonify({'status': status, 'slides_done': slides_done, 'total': total})


@app.route('/api/slide/<deck_id>/<int:slide_num>')
def serve_slide(deck_id, slide_num):
    path = get_slide_path(deck_id, slide_num)
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype='image/png')


@app.route('/api/vote', methods=['POST'])
def vote():
    data = request.json
    category = data['category']
    winner_id = data['winner_id']
    loser_id = data['loser_id']

    winner = get_deck(winner_id)
    loser = get_deck(loser_id)
    if not winner or not loser:
        return jsonify({'error': 'deck not found'}), 404

    new_winner_elo, new_loser_elo = update(winner['elo'], loser['elo'])
    record_vote(category, winner_id, loser_id, new_winner_elo, new_loser_elo)
    return jsonify({'success': True})


@app.route('/rankings/<category>')
def rankings(category):
    if category not in CATEGORIES:
        abort(404)
    decks = get_decks_by_category(category)
    total, matches = get_category_stats(category)
    return render_template('rankings.html',
                           category=category,
                           category_name=CATEGORIES[category],
                           decks=decks,
                           total_matches=matches,
                           all_categories=CATEGORIES)


@app.route('/api/scan', methods=['POST'])
def api_scan():
    count = scan()
    return jsonify({'scanned': count})


@app.route('/api/analyse/<category>', methods=['POST'])
def api_analyse(category):
    if category not in CATEGORIES:
        return jsonify({'error': 'unknown category'}), 404
    api_key = request.json.get('api_key', '').strip()
    if not api_key:
        return jsonify({'error': 'api_key required'}), 400
    try:
        from scorer import analyse_category
        results, removed = analyse_category(category, api_key)
        return jsonify({'results': results, 'removed': removed})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import socket
    init_db()
    print("Scanning for decks...")
    count = scan()
    print(f"Found {count} decks")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = '127.0.0.1'
    print(f"\n  Local:   http://127.0.0.1:{PORT}")
    print(f"  Network: http://{local_ip}:{PORT}  ← share this with your team\n")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
