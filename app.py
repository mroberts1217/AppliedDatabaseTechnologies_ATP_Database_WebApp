#!/usr/bin/env python
# coding: utf-8
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("atp.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return render_template("home.html")

# Use sqllite syntax to display all matches

@app.route("/matches")
def matches_list():
    conn = get_db()
    matches = conn.execute("""
        SELECT 
            m.match_id,
            m.tourney_id,
            m.match_num,
            w.player_name AS winner_name,
            l.player_name AS loser_name,
            m.score,
            m.round
        FROM matches m
        LEFT JOIN players w ON m.winner_id = w.player_id
        LEFT JOIN players l ON m.loser_id = l.player_id
        ORDER BY m.match_id DESC
        
    """).fetchall()
    conn.close()
    return render_template("matches_list.html", matches=matches)

@app.route("/matches/new", methods=["GET", "POST"])
def new_match():
    conn = get_db()

    if request.method == "POST":
        winner_id = request.form["winner_id"]
        loser_id = request.form["loser_id"]
        score = request.form["score"]
        round_ = request.form["round"]
        tourney_id = request.form["tourney_id"]

        conn.execute("""
            INSERT INTO matches (tourney_id, winner_id, loser_id, score, round)
            VALUES (?, ?, ?, ?, ?)
        """, (tourney_id, winner_id, loser_id, score, round_))

        conn.commit()
        conn.close()
        return redirect("/matches")

    # Load players + tournaments for dropdowns
    players = conn.execute("SELECT player_id, player_name FROM players ORDER BY player_name").fetchall()
    tournaments = conn.execute("SELECT tourney_id, tourney_name FROM tournaments ORDER BY tourney_date DESC").fetchall()
    conn.close()

    return render_template("new_match.html", players=players, tournaments=tournaments)

@app.route("/matches/<match_id>/edit", methods=["GET", "POST"])
def edit_match(match_id):
    conn = get_db()

    if request.method == "POST":
        winner_id = request.form["winner_id"]
        loser_id = request.form["loser_id"]
        score = request.form["score"]
        round_ = request.form["round"]

        conn.execute("""
            UPDATE matches
            SET winner_id = ?, loser_id = ?, score = ?, round = ?
            WHERE match_id = ?
        """, (winner_id, loser_id, score, round_, match_id))

        conn.commit()
        conn.close()
        return redirect(f"/match/{match_id}")

    # Load match + players
    match = conn.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
    players = conn.execute("SELECT player_id, player_name FROM players ORDER BY player_name").fetchall()
    conn.close()

    return render_template("edit_match.html", match=match, players=players)

@app.route("/matches/<match_id>/delete", methods=["POST"])
def delete_match(match_id):
    conn = get_db()
    conn.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
    conn.commit()
    conn.close()
    return redirect("/matches")

@app.route("/search")
def search():
    q = request.args.get("q", "")
    surface = request.args.get("surface", "")
    level = request.args.get("level", "")
    year = request.args.get("year", "")
    tournament = request.args.get("tournament", "")
    round_filter = request.args.get("round", "")

    conn = get_db()

    sql = """
        SELECT 
            m.match_id,
            m.tourney_id,              
            t.tourney_name,
            t.surface,
            t.tourney_level,
            substr(t.tourney_date, 1, 4) AS year,
            m.winner_id,
            m.loser_id,
            w.player_name AS winner_name,
            l.player_name AS loser_name,
            m.score,
            m.round
        FROM matches m
        LEFT JOIN players w ON m.winner_id = w.player_id
        LEFT JOIN players l ON m.loser_id = l.player_id
        LEFT JOIN tournaments t ON m.tourney_id = t.tourney_id
        WHERE 1=1
    """

    params = []

    if q:
        sql += " AND (w.player_name LIKE ? OR l.player_name LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]

    if tournament:
        sql += " AND t.tourney_name LIKE ?"
        params.append(f"%{tournament}%")

    if surface:
        sql += " AND t.surface = ?"
        params.append(surface)

    if level:
        sql += " AND t.tourney_level = ?"
        params.append(level)

    if year:
        sql += " AND substr(t.tourney_date, 1, 4) = ?"
        params.append(year)

    if round_filter:
        sql += " AND m.round = ?"
        params.append(round_filter)

    sql += " ORDER BY m.match_id DESC LIMIT 300"

    matches = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template(
        "search.html",
        matches=matches,
        q=q,
        surface=surface,
        level=level,
        year=year,
        tournament=tournament,
        round=round_filter
    )


@app.route("/player/<player_id>")
def player_profile(player_id):
    conn = get_db()

    # Get player info
    player = conn.execute("""
        SELECT *
        FROM players
        WHERE player_id = ?
    """, (player_id,)).fetchone()

    # Wins
    wins = conn.execute("""
        SELECT 
            m.*,
            t.tourney_name,
            t.surface,
            t.tourney_level,
            substr(t.tourney_date, 1, 4) AS year,
            l.player_name AS opponent_name,
            l.player_id AS loser_id
        FROM matches m
        JOIN players l ON m.loser_id = l.player_id
        JOIN tournaments t ON m.tourney_id = t.tourney_id
        WHERE m.winner_id = ?
        ORDER BY t.tourney_date DESC
    """, (player_id,)).fetchall()

    # Losses
    losses = conn.execute("""
        SELECT 
            m.*,
            t.tourney_name,
            t.surface,
            t.tourney_level,
            substr(t.tourney_date, 1, 4) AS year,
            w.player_name AS opponent_name,
            w.player_id AS winner_id
        FROM matches m
        JOIN players w ON m.winner_id = w.player_id
        JOIN tournaments t ON m.tourney_id = t.tourney_id
        WHERE m.loser_id = ?
        ORDER BY t.tourney_date DESC
    """, (player_id,)).fetchall()

    conn.close()

    return render_template("player.html", player=player, wins=wins, losses=losses)

@app.route("/headtohead")
def headtohead():
    p1 = request.args.get("p1", "")
    p2 = request.args.get("p2", "")
    surface = request.args.get("surface", "")
    level = request.args.get("level", "")
    year = request.args.get("year", "")
    round_filter = request.args.get("round", "")

    # If no players entered yet, just show the form
    if not p1 or not p2:
        return render_template(
            "headtohead.html",
            p1=p1, p2=p2,
            surface=surface, level=level, year=year, round=round_filter,
            matches=None,
            p1_name="", p2_name="",
            p1_wins=0, p2_wins=0
        )

    conn = get_db()

    # Look up both players
    p1_row = conn.execute("""
        SELECT player_id, player_name
        FROM players
        WHERE player_name LIKE ?
        LIMIT 1
    """, (f"%{p1}%",)).fetchone()

    p2_row = conn.execute("""
        SELECT player_id, player_name
        FROM players
        WHERE player_name LIKE ?
        LIMIT 1
    """, (f"%{p2}%",)).fetchone()

    if not p1_row or not p2_row:
        conn.close()
        return render_template(
            "headtohead.html",
            p1=p1, p2=p2,
            surface=surface, level=level, year=year, round=round_filter,
            matches=[],
            p1_name=p1_row["player_name"] if p1_row else "Not found",
            p2_name=p2_row["player_name"] if p2_row else "Not found",
            p1_wins=0, p2_wins=0
        )

    p1_id = p1_row["player_id"]
    p2_id = p2_row["player_id"]

    # Base SQL
    sql = """
        SELECT 
            m.match_id,
            w.player_name AS winner_name,
            l.player_name AS loser_name,
            m.winner_id,
            m.loser_id,
            m.tourney_id,
            t.tourney_name,
            t.surface,
            t.tourney_level,
            substr(t.tourney_date, 1, 4) AS year,
            m.score,
            m.round
        FROM matches m
        JOIN players w ON m.winner_id = w.player_id
        JOIN players l ON m.loser_id = l.player_id
        JOIN tournaments t ON m.tourney_id = t.tourney_id
        WHERE ((m.winner_id = ? AND m.loser_id = ?)
            OR (m.winner_id = ? AND m.loser_id = ?))
    """

    params = [p1_id, p2_id, p2_id, p1_id]

    # Apply filters
    if surface:
        sql += " AND t.surface = ?"
        params.append(surface)

    if level:
        sql += " AND t.tourney_level = ?"
        params.append(level)

    if year:
        sql += " AND substr(t.tourney_date, 1, 4) = ?"
        params.append(year)

    if round_filter:
        sql += " AND m.round = ?"
        params.append(round_filter)

    sql += " ORDER BY t.tourney_date DESC"

    matches = conn.execute(sql, params).fetchall()
    conn.close()

    # Count wins
    p1_wins = sum(1 for m in matches if m["winner_id"] == p1_id)
    p2_wins = sum(1 for m in matches if m["winner_id"] == p2_id)

    return render_template(
        "headtohead.html",
        p1=p1, p2=p2,
        surface=surface, level=level, year=year, round=round_filter,
        matches=matches,
        p1_name=p1_row["player_name"],
        p2_name=p2_row["player_name"],
        p1_wins=p1_wins,
        p2_wins=p2_wins
    )
@app.route("/match/<match_id>")
def match_detail(match_id):
    conn = get_db()

    # Match info + players + tournament
    match = conn.execute("""
        SELECT 
            m.*,
            w.player_name AS winner_name,
            l.player_name AS loser_name,
            t.tourney_name,
            t.surface,
            t.tourney_level,
            substr(t.tourney_date, 1, 4) AS year
        FROM matches m
        JOIN players w ON m.winner_id = w.player_id
        JOIN players l ON m.loser_id = l.player_id
        JOIN tournaments t ON m.tourney_id = t.tourney_id
        WHERE m.match_id = ?
    """, (match_id,)).fetchone()

    # Match statistics
    stats = conn.execute("""
        SELECT *
        FROM match_stats
        WHERE match_id = ?
    """, (match_id,)).fetchone()

    conn.close()

    return render_template("match.html", match=match, stats=stats)

@app.route("/tournament/<tourney_id>")
def tournament_detail(tourney_id):
    conn = get_db()

    # Read round filter from query string
    round_filter = request.args.get("round", "")

    # Tournament info
    t = conn.execute("""
        SELECT 
            tourney_id,
            tourney_name,
            surface,
            draw_size,
            tourney_level,
            tourney_date,
            substr(tourney_date, 1, 4) AS year
        FROM tournaments
        WHERE tourney_id = ?
    """, (tourney_id,)).fetchone()

    #Base SQL for matches
    sql = """
        SELECT 
            m.match_id,
            m.tourney_id,
            t.tourney_name,
            t.surface,
            t.tourney_level,
            substr(t.tourney_date, 1, 4) AS year,
            w.player_name AS winner_name,
            l.player_name AS loser_name,
            m.score,
            m.round,
            m.winner_id,
            m.loser_id,
            m.winner_rank,
            m.loser_rank,
            m.winner_rank_points,
            m.loser_rank_points,
            m.winner_age,
            m.loser_age,
            m.minutes
        FROM matches m
        JOIN players w ON m.winner_id = w.player_id
        JOIN players l ON m.loser_id = l.player_id
        JOIN tournaments t ON m.tourney_id = t.tourney_id
        WHERE m.tourney_id = ?
    """

    params = [tourney_id]

    # Apply filter if selected
    if round_filter:
        sql += " AND m.round = ?"
        params.append(round_filter)

    sql += " ORDER BY m.round"

    matches = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template("tournament.html", t=t, matches=matches, round=round_filter)




if __name__ == "__main__":
    app.run(debug=True)