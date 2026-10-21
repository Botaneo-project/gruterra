"""Durable PC-side watering checks; a planned time is never a measurement time."""
from datetime import datetime,timedelta
import database
from contextlib import closing


def due_requests(now=None):
    now=now or datetime.now()
    database.initialiser_collectes_prioritaires()
    with closing(database.get_connection()) as db:
        rows=db.execute("SELECT id,plante_id,date_prevue,statut,derniere_tentative FROM collectes_prioritaires WHERE date_prevue IS NOT NULL AND raison IN ('post_arrosage','post_arrosage_10min') AND statut IN ('en_attente','echec','en_cours') ORDER BY date_prevue,id").fetchall()
    result=[]
    for ident,plant,due,status,last in rows:
        try:
            if datetime.fromisoformat(due)>now:continue
            if last and (now-datetime.fromisoformat(last)).total_seconds() < (300 if status=='en_cours' else 60):continue
        except (ValueError,TypeError):continue
        result.append((ident,plant))
    return result[:5]


def claim(request_id,now=None):
    now=now or datetime.now()
    database.initialiser_collectes_prioritaires()
    with closing(database.get_connection()) as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT date_prevue,statut,derniere_tentative FROM collectes_prioritaires WHERE id=?',(request_id,)).fetchone()
        if not row:return False
        due,status,last=row
        if status=='reussie':return False
        if due and datetime.fromisoformat(due)>now:return False
        if last and (now-datetime.fromisoformat(last)).total_seconds() < (300 if status=='en_cours' else 60):return False
        db.execute("UPDATE collectes_prioritaires SET statut='en_cours',derniere_tentative=? WHERE id=?",(now.isoformat(timespec='seconds'),request_id))
        db.commit()
        return True
