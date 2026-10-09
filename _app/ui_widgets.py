"""Icônes locales de langue, indépendantes du rendu des emojis Windows."""
import tkinter as tk


def creer_drapeau(master, code, largeur=24, hauteur=16):
    image = tk.PhotoImage(master=master, width=largeur, height=hauteur)
    for y in range(hauteur):
        ligne = []
        for x in range(largeur):
            if code == "fr":
                couleur = ("#002395", "#FFFFFF", "#ED2939")[min(2, x * 3 // largeur)]
            else:
                dx = abs(x - (largeur - 1) / 2)
                dy = abs(y - (hauteur - 1) / 2)
                diagonale = min(abs(y - x * hauteur / largeur), abs(y - (largeur - 1 - x) * hauteur / largeur))
                couleur = "#012169"
                if diagonale < 2 or dx < 4 or dy < 3:
                    couleur = "#FFFFFF"
                if diagonale < 0.7 or dx < 2 or dy < 1.5:
                    couleur = "#C8102E"
            ligne.append(couleur)
        image.put("{" + " ".join(ligne) + "}", to=(0, y))
    return image
