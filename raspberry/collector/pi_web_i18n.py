"""Translate trusted page templates only; never translate sensor data or API keys."""
import json
import re
from http.cookies import SimpleCookie
from urllib.parse import urlsplit, parse_qs

EN = {
'Gruterra · Historique météo':'Gruterra · Weather history',
'← Retour aux capteurs':'← Back to sensors','Historique météo':'Weather history',
'Relevés conservés sur ce Raspberry. Les cumuls de pluie ne sont pas additionnés. Plusieurs versions d’une mesure peuvent apparaître.':'Readings stored on this Raspberry. Rain accumulations are not added together. Multiple versions of a reading may appear.',
'Toutes les stations':'All stations','Mesure':'Measurement','Toutes les mesures':'All measurements','Période de mesure':'Measurement period','Tout l’historique disponible':'All available history','Dernières 24 heures':'Last 24 hours','7 derniers jours':'Last 7 days','30 derniers jours':'Last 30 days','Actualiser l’historique':'Refresh history','Chargement…':'Loading…',
'Actualiser consulte le stockage local sans lancer de collecte Netatmo. Les dates sont affichées dans le fuseau du téléphone. Une station voisine ne mesure pas exactement la pluie chez vous.':'Refresh reads local storage without starting Netatmo collection. Dates use the phone time zone. A nearby station does not measure the exact rainfall at your home.',
'Date inconnue':'Unknown date','Pluie · cumul sur 1 heure':'Rain · 1-hour accumulation','Pluie · cumul sur 24 heures':'Rain · 24-hour accumulation','Pluie · cumul source 1 h':'Rain · source 1-hour accumulation','Pluie · cumul source 24 h':'Rain · source 24-hour accumulation','Pluie · mesure source':'Rain · source reading','Pluie':'Rain','Température':'Temperature','Humidité':'Humidity','Pression':'Pressure','Vitesse du vent':'Wind speed',
' version(s) correspondant aux filtres, parmi les ':' version(s) matching the filters, among the last ',' dernières versions chargées.':' loaded versions.',
'Donnée absente':'Missing data','Mesurée : ':'Measured: ','Station : ':'Station: ','Publique':'Public','Personnelle':'Personal','Cumul glissant':'Rolling accumulation','Mesure instantanée':'Instantaneous reading','Journée civile':'Calendar day','Période non précisée':'Unspecified period','Du ':'From ',' au ':' to ','Récupérée : ':'Retrieved: ','Réception PC confirmée':'PC receipt confirmed','En attente de confirmation PC':'Awaiting PC confirmation','Module : ':'Module: ',
'Aucun relevé ne correspond aux filtres. Essayez une autre période ou une autre mesure.':'No readings match these filters. Try another period or measurement.',
'Aucune station enregistrée':'No stored stations','Aucune mesure enregistrée':'No stored measurements',' version(s) affichée(s) sur ':' version(s) displayed out of ',' enregistrée(s), par ordre de stockage récent.':' stored, newest stored first.',
'Votre historique météo est vide. Les stations et les filtres seront disponibles après le premier relevé. Actualiser ne déclenche pas de collecte : son accès Netatmo doit être configuré et validé.':'Your weather history is empty. Stations and filters become available after the first reading. Refresh does not start collection: Netatmo access must be configured and validated.',
'Historique indisponible. Vérifiez la connexion au Raspberry puis réessayez. Les données éventuellement affichées ne sont plus actualisées.':'History unavailable. Check the Raspberry connection and retry. Any displayed data is no longer being refreshed.',
'Votre collecteur Raspberry':'Your Raspberry collector','Consulter l’historique météo →':'View weather history →','Prévisions Météo-France':'Météo-France forecast','Modèle AROME France via ':'AROME France model via ',' · lieu configuré dans Gruterra, même en déplacement.':' · location configured in Gruterra, including while travelling.','Afficher les prochaines 24 heures':'Show the next 24 hours',
'Prévisions, pas observations. Pluie : cumul prévu sur l’heure précédant l’échéance affichée. La première période peut être en partie écoulée. Cache renouvelé à la consultation, au plus une fois par heure.':'Forecasts, not observations. Rain: predicted accumulation during the hour preceding the displayed time. The first period may already be partly elapsed. Cache refreshed on request, at most once an hour.',
'Lire les capteurs maintenant':'Read sensors now','Synchronisation PC':'PC synchronization','Les relevés restent conservés sur le Raspberry. Le PC les récupère lorsque Gruterra est ouvert et que les deux appareils peuvent communiquer.':'Readings remain stored on the Raspberry. The PC retrieves them when Gruterra is open and both devices can communicate.','Actualiser l’affichage':'Refresh display',
'Actualiser affiche les données déjà enregistrées. « Lire les capteurs » demande une nouvelle lecture, qui peut prendre plusieurs minutes. Actualisation automatique tant que cette page est visible.':'Refresh displays existing readings. “Read sensors” requests new readings, which may take several minutes. The display refreshes automatically while this page is visible.',
'Aucune':'None','Date à vérifier':'Date needs checking','À l’instant':'Just now','Il y a ':'Elapsed: ',' j':' d',
'Historique pendant l’éclairage':'Lighting-period history','Allumage':'Lights on','Extinction':'Lights off','Enregistrer les horaires':'Save lighting times','Horaires enregistrés sur le Pi.':'Lighting times saved on the Pi.','Horaires proposés, à enregistrer.':'Suggested times, not yet saved.',
'Enregistrement impossible : vérifiez les heures et la connexion.':'Unable to save: check the times and connection.',' · moyenne ':' · average ',' relevé(s)':' reading(s)','Minimum ':'Minimum ',' lux · maximum ':' lux · maximum ','Aucun relevé dans la plage choisie.':'No readings in the selected lighting period.',
'Heures de Paris · 7 derniers jours disponibles. Zéros inclus, sans interpolation. Horaires actuels appliqués à tous les jours affichés ; horaires partagés à la prochaine synchronisation avec le PC.':'Paris time · last 7 available days. Zeros included, without interpolation. Current lighting times apply to all displayed days; times are shared on the next PC synchronization.',
'Copier les données du jour':'Copy today’s data','Données journalières à copier':'Daily data to copy','Relevés du jour — heures de Paris':'Daily readings — Paris time','Éclairage prévu : ':'Scheduled lighting: ','Les deux sources sont listées séparément ; elles peuvent se chevaucher.':'Both sources are listed separately; they may overlap.','Date et heure;Source;Qualité date;Température °C;Humidité sol %;Lumière lux;Conductivité µS/cm':'Date and time;Source;Date quality;Temperature °C;Soil moisture %;Light lux;Conductivity µS/cm','Dernier bilan éclairage ':'Latest lighting summary ',' : moyenne ':': average ',' relevés':' readings','absent':'missing','Aucun relevé aujourd’hui.':'No readings today.','Données copiées.':'Data copied.','Appuyez longuement dans le texte, puis choisissez Copier.':'Press and hold the text, then choose Copy.',
'Évolution des mesures':'Measurement trends','Période du graphique de lumière':'Light chart period','Aujourd’hui':'Today','Hier':'Yesterday','7 jours':'7 days','Mesure du graphique':'Chart measurement','Lumière':'Light','Humidité du sol':'Soil moisture','Touchez un point pour voir sa valeur.':'Tap a point to see its value.',
'Heures de Paris · dates estimées pour l’historique du capteur. Une coupure de plus de 90 minutes interrompt la courbe. Les points représentent uniquement les mesures disponibles.':'Paris time · sensor history dates are estimated. Gaps longer than 90 minutes break the line. Points represent available readings only.',
'Historique indisponible.':'History unavailable.',' relevé(s) · ':' reading(s) · ','historique du capteur':'sensor history','lectures ponctuelles':'spot readings','Aucun relevé pour cette période.':'No readings for this period.',' en ':' in ',
'Raspberry joignable · ':'Raspberry connected · ','Lecture en cours…':'Reading in progress…','Demande en attente…':'Request pending…','Le Raspberry lit les capteurs. Les valeurs précédentes restent visibles.':'The Raspberry is reading the sensors. Previous values remain visible.','Demande reçue. En attente du collecteur…':'Request received. Waiting for the collector…','Capteur ':'Sensor ','En attente de première mesure':'Waiting for the first reading','Conductivité':'Conductivity','Dernier relevé : ':'Latest reading: ','Date non confirmée : horloge du Raspberry à vérifier.':'Unconfirmed date: check the Raspberry clock.','Relevé ancien : plus de 12 heures.':'Old reading: more than 12 hours ago.','Aucune mesure disponible.':'No measurements available.',
'Aujourd’hui · lumière et moyennes':'Today · light and averages','Lumière moyenne mesurée':'Average measured light','Maximum mesuré':'Measured maximum','Température moyenne':'Average temperature','Humidité du sol moyenne':'Average soil moisture',' relevé(s) · du ':' reading(s) · from ',
'Journée définie en heure de Paris. Moyennes des relevés disponibles, nuit comprise : elles ne représentent pas nécessairement toute la journée. ':'Day defined in Paris time. Averages use available readings, including nighttime: they may not represent the whole day. ',
'Historique du capteur, dates estimées depuis son horloge.':'Sensor history, dates estimated from its clock.','Lectures ponctuelles uniquement.':'Spot readings only.','Pas encore de relevé daté pour aujourd’hui.':'No dated readings for today yet.','Dernière collecte en échec. Les dernières valeurs sont conservées.':'Last collection failed. Previous readings are retained.','Détails du capteur':'Sensor details','Dernière tentative : ':'Last attempt: ','Dernière réussite : ':'Last success: ','Aucun capteur enregistré.':'No sensors registered.',
' relevé(s) en attente de confirmation du PC · ':' reading(s) awaiting PC confirmation · ',' relevé(s) historiques conservés.':' historical reading(s) stored.','Connexion interrompue · les valeurs affichées ne sont plus actualisées.':'Connection interrupted · displayed values are no longer refreshed.',
'Actualisation indisponible. Dernière copie conservée. ':'Refresh unavailable. Last cached copy retained. ','Consultée le ':'Retrieved on ',' · heure du calcul non fournie.':' · model run time not supplied.','Aucune prévision disponible.':'No forecast available.','Pluie prévue sur 1 h':'Forecast rain over 1 hour','Humidité de l’air':'Air humidity','Vent':'Wind','Rafales':'Gusts','Indisponible':'Unavailable','Aucune échéance future disponible.':'No future forecast times available.','Prévisions indisponibles. Réessayez plus tard.':'Forecast unavailable. Try again later.','Envoi de la demande…':'Sending request…','Demande non confirmée. Actualisez la page pour vérifier son état.':'Request not confirmed. Refresh the page to check its status.',
'Collecte terminée.':'Collection completed.','Collecte terminée avec une erreur : voir le capteur.':'Collection completed with an error: check the sensor.','Collecteur en attente.':'Collector waiting.','Lecture des capteurs en cours…':'Reading sensors…',
}

EN.update({'Afficher / actualiser la météo': 'Show / refresh forecast', 'Prochaines 24 heures': 'Next 24 hours', 'Températures prévues · minimum / maximum': 'Forecast temperatures · minimum / maximum', 'Prévisions heure par heure': 'Hourly forecast', 'Faites défiler les heures ou touchez le graphique.': 'Scroll through the hours or tap the chart.', 'Température en courbe et pluie en barres sur 24 heures': 'Temperature line and rainfall bars over 24 hours'})

EN.update({'Demain':'Tomorrow','Période de pluie : ':'Rain period: ','Actualisation impossible. Les prévisions éventuellement affichées ne sont plus actualisées.':'Unable to refresh. Any forecasts still displayed are no longer being updated.'})

EN.update({'Heures de Paris · 7 derniers jours disponibles. Zéros inclus, sans interpolation. Changements datés par jour d’allumage ; les jours précédents conservent leur plage. Horaires partagés avec le PC.':'Paris time · last 7 available days. Zeros included, without interpolation. Changes are dated by lighting day; previous days keep their settings. Times are shared with the PC.'})

def language(path, cookie=''):
    query=parse_qs(urlsplit(path).query).get('lang',[''])[0]
    if query in ('fr','en'):return query
    try:
        jar=SimpleCookie();jar.load(cookie)
        saved=jar.get('gruterra_lang')
        return saved.value if saved and saved.value in ('fr','en') else 'fr'
    except Exception:return 'fr'

def render(template, lang):
    # Only trusted literal UI strings are translated; values inserted later remain intact.
    parts=template.split('<script>')
    if lang=='en':
        parts[0]=re.sub(r'>([^<>]+)<',lambda m:'>'+EN.get(m[1],m[1])+'<',parts[0])
        parts[0]=parts[0].replace('lang="fr"','lang="en"')
        for i in range(1,len(parts)):
            parts[i]=re.sub(r"'((?:\\.|[^'\\])*)'",lambda m:json.dumps(EN[m[1]],ensure_ascii=False) if m[1] in EN else m[0],parts[i])
            parts[i]=parts[i].replace("'fr-FR'","'en-GB'")
    page='<script>'.join(parts)
    caption='Langue' if lang=='fr' else 'Language'
    nav=f'<nav aria-label="{caption}" style="padding:12px 18px;max-width:650px;margin:auto"><span>{caption} : </span><a href="?lang=fr" lang="fr" style="display:inline-block;padding:12px"'+(' aria-current="true"' if lang=='fr' else '')+'>Français</a> · <a href="?lang=en" lang="en" style="display:inline-block;padding:12px"'+(' aria-current="true"' if lang=='en' else '')+'>English</a></nav>'
    page=page.replace('<main>',nav+'<main>',1)
    return page
