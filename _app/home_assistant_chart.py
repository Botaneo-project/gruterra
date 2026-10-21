"""Readable HA timelines: separate units, real timestamps, no interpolation."""
from datetime import datetime
from zoneinfo import ZoneInfo
import math


def chart_data(rows, metric, *, full_scale=False):
    points=[]
    for row in rows:
        value=row.get('value')
        if row.get('metric')!=metric or isinstance(value,bool):continue
        # HA archive preserves numeric states as decimal strings.
        try:value=float(value)
        except (ValueError,TypeError,OverflowError):continue
        if not math.isfinite(value):continue
        if row.get('status') not in (None,'available') or not row.get('usable_for_timeline',True):continue
        if row.get('timing_kind') in ('ha_attribute_update','initial_state_uncertain'):continue
        try:stamp=datetime.fromisoformat(row['ha_updated_at']).timestamp()
        except (ValueError,TypeError,KeyError):continue
        points.append((stamp,float(value),row['hardware_id']))
    points.sort()
    if not points:return None
    lo=min(p[1] for p in points);hi=max(p[1] for p in points)
    pad=max(1,(hi-lo)*.15)
    if metric in ('soil_moisture','air_humidity') and full_scale:
        lo=min(0,lo);hi=max(100,hi)
    else:
        lo-=pad;hi+=pad
        if metric in ('soil_moisture','air_humidity','illuminance'):lo=max(0,lo)
        if metric in ('soil_moisture','air_humidity'):hi=min(100,hi)
        if hi<=lo:hi=lo+1
    # Round to readable graduations rather than arbitrary decimal bounds.
    raw=(hi-lo)/4
    magnitude=10**math.floor(math.log10(raw))
    step=next(v*magnitude for v in (1,2,2.5,5,10) if v*magnitude>=raw)
    lo=math.floor(lo/step)*step;hi=math.ceil(hi/step)*step
    start=points[0][0];end=points[-1][0]
    if start==end:start-=1800;end+=1800
    return {'points':points,'low':lo,'high':hi,'start':start,'end':end,'step':step}


def group_bursts(points, *, seconds=1):
    """Display-only groups bounded from first state, isolated by hardware.

    A burst is not a confirmed physical measurement. All members remain available.
    """
    grouped=[]
    for device in sorted({point[2] for point in points}):
        series=sorted(p for p in points if p[2]==device)
        current=[]
        for point in series:
            if current and point[0]-current[0][0]>=seconds:
                grouped.append(current);current=[]
            current.append(point)
        if current:grouped.append(current)
    return sorted(grouped,key=lambda group:group[-1][0])


def draw_chart(canvas, rows, metric, palette, t, *, full_scale=False, raw_states=False, conversion_notes=()):
    canvas.delete('all')
    model=chart_data(rows,metric,full_scale=full_scale)
    text=palette['TEXT'];muted=palette.get('SECONDARY',text)
    width=max(320,canvas.winfo_width());height=max(280,canvas.winfo_height())
    if not model:
        if int(float(canvas.cget('height')))!=340:canvas.configure(height=340)
        canvas.create_text(16,24,anchor='nw',text=t('ha_view_empty'),fill=text)
        canvas.bind('<Motion>',lambda e:None)
        return
    units={'soil_moisture':'%','air_humidity':'%','temperature':'°C','illuminance':'lux'}
    unit=units[metric]
    devices=sorted({p[2] for p in model['points']})
    colors=['#3686c9','#c37423','#9b6bcc','#249681','#c94e67']
    device_colors={device:colors[i%len(colors)] for i,device in enumerate(devices)}
    canvas.create_text(12,8,anchor='nw',text=t('ha_metric_'+metric)+' ('+unit+')',fill=text,font=('Segoe UI',11,'bold'))
    legend_columns=max(1,int((width-24)//260))
    legend_rows=math.ceil(len(devices)/legend_columns)
    top=64+20*legend_rows
    required_height=max(340,top+52+160)
    if int(float(canvas.cget('height')))!=required_height:
        canvas.configure(height=required_height)
    height=max(height,required_height)
    bottom=height-52;left=68;right=width-22
    for i,device in enumerate(devices):
        x=14+(i%legend_columns)*260;y=34+(i//legend_columns)*20
        canvas.create_oval(x,y+3,x+8,y+11,fill=device_colors[device],outline='')
        canvas.create_text(x+16,y,anchor='nw',text=device,fill=text,font=('Segoe UI',9))
    def fmt(value):return f'{value:.1f}'.rstrip('0').rstrip('.') if abs(value)<1000 else f'{value:,.0f}'.replace(',',' ')
    def local(stamp,full=False):return datetime.fromtimestamp(stamp,ZoneInfo('Europe/Paris')).strftime('%d/%m/%Y %H:%M:%S' if full else '%d/%m %H:%M')
    count=max(1,round((model['high']-model['low'])/model['step']))
    for i in range(count+1):
        value=model['low']+(model['high']-model['low'])*i/count
        y=bottom-(bottom-top)*i/count
        canvas.create_line(left,y,right,y,fill=palette.get('BORDER',muted))
        canvas.create_text(left-8,y,anchor='e',text=fmt(value),fill=muted,font=('Segoe UI',9))
    ticks=3 if width<650 else 5
    for i in range(ticks):
        stamp=model['start']+(model['end']-model['start'])*i/(ticks-1)
        x=left+(right-left)*i/(ticks-1)
        canvas.create_line(x,top,x,bottom,fill=palette.get('BORDER',muted))
        canvas.create_text(x,bottom+10,anchor='n',text=local(stamp).replace(' ','\n'),fill=muted,font=('Segoe UI',8))
    canvas.create_text(right,height-2,anchor='se',text=t('ha_chart_local_time'),fill=muted,font=('Segoe UI',8))
    if metric=='illuminance':
        for note in conversion_notes:
            if model['start']<=note['at']<=model['end']:
                x=left+(right-left)*(note['at']-model['start'])/(model['end']-model['start'])
                canvas.create_line(x,top,x,bottom,fill=palette.get('ORANGE','#c37423'),dash=(5,3),width=2)
                canvas.create_text(min(right-70,max(left+70,x)),top+12,text=t('ha_chart_conversion_marker'),fill=text,font=('Segoe UI',9,'bold'))
    plotted=[]
    groups=[[point] for point in model['points']] if raw_states else group_bursts(model['points'])
    def y_for(value):return bottom-(bottom-top)*(value-model['low'])/(model['high']-model['low'])
    for group in groups:
        stamp,value,device=group[-1]
        x=left+(right-left)*(stamp-model['start'])/(model['end']-model['start'])
        y=y_for(value)
        values=[point[1] for point in group]
        if len(set(values))>1:
            color=palette.get('ORANGE','#c37423')
            y1=y_for(min(values));y2=y_for(max(values))
            canvas.create_line(x,y1,x,y2,fill=color,width=2)
            for tip in (y1,y2):canvas.create_line(x-4,tip,x+4,tip,fill=color,width=2)
            canvas.create_rectangle(x-3,y-3,x+3,y+3,outline=color,fill=palette['CARD'])
        else:
            canvas.create_oval(x-3,y-3,x+3,y+3,fill=device_colors[device],outline=palette['CARD'])
        for original_stamp,original_value,original_device in group:
            plotted.append((x,y_for(original_value),original_stamp,original_value,original_device))
    def hover(event):
        canvas.delete('tooltip')
        nearest=min(plotted,key=lambda p:(p[0]-event.x)**2+(p[1]-event.y)**2)
        x,y,stamp,value,device=nearest
        if (x-event.x)**2+(y-event.y)**2>144:return
        nearby=[p for p in plotted if abs(p[0]-x)<5 and p[4]==device]
        label='\n'.join(f'{local(p[2],True)} · {fmt(p[3])} {unit}' for p in nearby[:6])+'\n'+device
        if len(nearby)>6:label+='\n…'
        item=canvas.create_text(min(width-12,max(12,event.x)),max(top,event.y-12),anchor='se' if event.x>width/2 else 'sw',text=label,fill=text,font=('Segoe UI',9,'bold'),tags='tooltip')
        bounds=canvas.bbox(item)
        box=canvas.create_rectangle(bounds[0]-6,bounds[1]-4,bounds[2]+6,bounds[3]+4,fill=palette['CARD'],outline=palette.get('BORDER',text),tags='tooltip')
        canvas.tag_raise(item,box)
    canvas.bind('<Motion>',hover)
    canvas.bind('<Leave>',lambda event:canvas.delete('tooltip'))
