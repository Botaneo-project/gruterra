"""Shared main-interface palettes; no Tk window or configuration side effects."""

THEME_CLAIR = {'BG': '#F2F6F1',
 'CARD': '#FBFDF9',
 'TEXT': '#223228',
 'SECONDARY': '#68786E',
 'GREEN': '#3F7F52',
 'LIGHT_GREEN': '#E4F1E7',
 'ORANGE': '#C77D25',
 'LIGHT_ORANGE': '#FFF0D8',
 'RED': '#B94A48',
 'LIGHT_RED': '#F8E1E0',
 'BORDER': '#D6E2D8',
 'BLUE': '#3F6F99',
 'LIGHT_BLUE': '#E4EEF7'}

THEME_SOMBRE = {'BG': '#111816',
 'CARD': '#1B2521',
 'TEXT': '#E8F0EA',
 'SECONDARY': '#9FB0A6',
 'GREEN': '#82C990',
 'LIGHT_GREEN': '#203B2A',
 'ORANGE': '#F0B35D',
 'LIGHT_ORANGE': '#3B2C1C',
 'RED': '#EF7979',
 'LIGHT_RED': '#3A2224',
 'BORDER': '#30423A',
 'BLUE': '#8DBAF0',
 'LIGHT_BLUE': '#203044'}


def history_palette(dark=False):
    base = THEME_SOMBRE if dark else THEME_CLAIR
    return {**base, 'GRID': base['BORDER'],
            'PURPLE': '#B8A7F4' if dark else '#6B55A3',
            'WATER': '#65C7FF' if dark else '#2C9FD6'}


def readable_text(background):
    value = background.lstrip('#')
    channels = [int(value[index:index+2], 16)/255 for index in (0, 2, 4)]
    linear = [channel/12.92 if channel<=0.04045 else ((channel+0.055)/1.055)**2.4 for channel in channels]
    luminance = sum(channel*weight for channel,weight in zip(linear, (0.2126,0.7152,0.0722)))
    return '#000000' if (luminance+0.05)/0.05 >= 1.05/(luminance+0.05) else '#FFFFFF'
