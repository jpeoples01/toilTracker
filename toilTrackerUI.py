import streamlit as st
from datetime import date, timedelta, datetime, time as dtime
from zoneinfo import ZoneInfo

def now_london():
    return datetime.now(ZoneInfo('Europe/London'))
import calendar
import json
import os

st.title('TOIL Tracker')

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput, .stNumberInput,
.stSelectbox, .stRadio, .stButton, .stMetric, .stTabs, p, div, span, label {
    font-family: 'JetBrains Mono', monospace !important;
}

h1, h2, h3 {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-size: 0.75rem;
}

.stMetric label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.stMetric [data-testid="metric-container"] div {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700;
}

button[kind="primary"], button[kind="secondary"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

RED_DIVIDER = '<hr style="border:none; border-top: 1px solid #E63946; margin: 1rem 0;">'
WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER", "local")

LOG_FILE = f"toil_log_{WORKER_ID}.json"
CLOCK_FILE = f"clock_log_{WORKER_ID}.json"


def to_minutes(h):
    # Convert safely via string to avoid float precision bugs
    h_str = f"{h:.2f}"
    hours_str, minutes_str = h_str.split(".")

    hours = int(hours_str)
    minutes = int(minutes_str)

    if minutes >= 60:
        st.error(f"Invalid input: {h} (minutes must be < .60)")
        st.stop()

    return hours * 60 + minutes


def last_friday_of_month(year, month):
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    offset = (last_day.weekday() - 4) % 7
    return last_day - timedelta(days=offset)

def get_pay_period(year, month):
    payday = last_friday_of_month(year, month)
    period_end = payday - timedelta(weeks=1)
    period_end_monday = period_end - timedelta(days=4)
    for num_weeks in [5, 4, 3]:
        start = period_end_monday - timedelta(weeks=num_weeks - 1)
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_payday = last_friday_of_month(prev_year, prev_month)
        prev_period_end = prev_payday - timedelta(weeks=1)
        if start > prev_period_end:
            return start, period_end, payday, num_weeks
    return period_end_monday, period_end, payday, 4

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {'entries': [], 'hours_used': 0.0, 'standard_day': 8}

def save_log(log):
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def load_clock():
    today = now_london().strftime('%Y-%m-%d')
    if os.path.exists(CLOCK_FILE):
        with open(CLOCK_FILE, 'r') as f:
            data = json.load(f)
        # auto-reset if the saved date is not today
        if data.get('date') == today:
            return data
    return {'date': today, 'events': [], 'work_pattern': '5 days / 40 hours (8h day)'}

def save_clock(data):
    with open(CLOCK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def time_to_minutes(t):
    return t.hour * 60 + t.minute

def minutes_to_time_str(total_minutes):
    total_minutes = total_minutes % (24 * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    suffix = 'am' if h < 12 else 'pm'
    display_h = h if h <= 12 else h - 12
    if display_h == 0:
        display_h = 12
    return f'{display_h}:{m:02d}{suffix}'

tab1, tab2, tab3 = st.tabs(['TOIL Monthly Tracker', 'TOIL Annual Leave Accruement', 'Hours Today'])

with tab1:
    work_pattern_tab1 = st.radio('Working pattern', ['5 days / 40 hours', '4 days / 40 hours'], key='pattern_tab1')

    if work_pattern_tab1 == '5 days / 40 hours':
        standard_day_tab1 = 8
    else:
        standard_day_tab1 = 10

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)
    st.subheader('Pay period')
    st.caption("Enter hours in HH.MM format (e.g. 38.30 = 38h 30m). Minutes must be less than 60.")

    today = date.today()
    months = [date(today.year, m, 1).strftime('%B %Y') for m in range(1, 13)]
    months += [date(today.year + 1, 1, 1).strftime('%B %Y')]

    default_month_idx = today.month - 1
    selected_month_str = st.selectbox('Select pay period month', months, index=default_month_idx)

    selected_date = date(int(selected_month_str.split(' ')[1]), list(calendar.month_name).index(selected_month_str.split(' ')[0]), 1)
    period_start, period_end, payday, num_weeks = get_pay_period(selected_date.year, selected_date.month)

    st.markdown(f"""
<div style="display:flex; gap:2rem; margin: 0.5rem 0 0.75rem; padding: 0.75rem 1rem; border-left: 3px solid #E63946; background-color: rgba(230, 57, 70, 0.08); border-radius: 0 4px 4px 0;">
    <div>
        <div style="font-size:0.65rem; letter-spacing:1px; text-transform:uppercase; opacity:0.6;">Period start</div>
        <div style="font-size:0.85rem; font-weight:500;">{period_start.strftime('%d %b %Y')}</div>
    </div>
    <div>
        <div style="font-size:0.65rem; letter-spacing:1px; text-transform:uppercase; opacity:0.6;">Period end</div>
        <div style="font-size:0.85rem; font-weight:500;">{period_end.strftime('%d %b %Y')}</div>
    </div>
    <div>
        <div style="font-size:0.65rem; letter-spacing:1px; text-transform:uppercase; opacity:0.6;">Payday</div>
        <div style="font-size:0.85rem; font-weight:500;">{payday.strftime('%d %b %Y')}</div>
    </div>
    <div>
        <div style="font-size:0.65rem; letter-spacing:1px; text-transform:uppercase; opacity:0.6;">Weeks</div>
        <div style="font-size:0.85rem; font-weight:500;">{num_weeks}</div>
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    hours = []
    holiday_days = []
    for i in range(num_weeks):
        week_start = period_start + timedelta(weeks=i)
        week_end = week_start + timedelta(days=4)
        col1, col2 = st.columns([3, 1])
        col1.markdown(f'**Week {i + 1}** — {week_start.strftime("%d %b")} to {week_end.strftime("%d %b")}')
        col2.markdown('&nbsp;', unsafe_allow_html=True)
        h = col1.number_input('Hours worked', min_value=0.0, max_value=168.0, step=0.01, format='%.2f', key=f'month_week_{i}')
        hd = col2.number_input('Holiday days', min_value=0, max_value=7, step=1, key=f'month_hols_{i}')
        hours.append(h)
        holiday_days.append(hd)

    if st.button('Calculate', key='monthly_calc'):
        total_holiday_minutes = sum(hd * standard_day_tab1 * 60 for hd in holiday_days)
        total_worked_minutes = sum(to_minutes(h) for h in hours)
        total_minutes = total_worked_minutes + total_holiday_minutes

        holiday_total_days = sum(holiday_days)
        if holiday_total_days > 0:
            st.info(f'Holiday hours added: {holiday_total_days} day(s) × {standard_day_tab1}h = {holiday_total_days * standard_day_tab1}h')

        st.write(f'**Total hours this month (worked + holiday):** {total_minutes // 60} hours and {total_minutes % 60} minutes')

        targets = {3: 120, 4: 160, 5: 200}
        leftMinutes = (targets[num_weeks] * 60) - total_minutes

        if leftMinutes > 0:
            st.error(f'You have {leftMinutes // 60} hours & {leftMinutes % 60} minutes left to work to get full pay')
        elif leftMinutes == 0:
            st.success('You have worked exactly your full hours this month!')
        else:
            overtimeMinutes = abs(leftMinutes)
            st.success(f'You have worked {overtimeMinutes // 60} hours & {overtimeMinutes % 60} minutes of overtime this month!')

with tab2:
    log = load_log()

    work_pattern = st.radio('Working pattern', ['5 days / 40 hours', '4 days / 40 hours'], key='pattern_tab2',
                            index=0 if log['standard_day'] == 8 else 1)

    if work_pattern == '5 days / 40 hours':
        standard_day = 8
    else:
        standard_day = 10

    log['standard_day'] = standard_day
    save_log(log)

    st.caption(f'Qualification for Annual TOIL: {standard_day}h work day with 3h+ overtime accrued (e.g. {standard_day + 3} hours worked in a day)')

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    total_banked = sum(e['overtime_hours'] for e in log['entries'])
    total_remaining = total_banked - log['hours_used']

    col1, col2, col3 = st.columns(3)
    col1.metric('Hours banked', f"{total_banked:.1f}h")
    col2.metric('Hours used', f"{log['hours_used']:.1f}h")
    col3.metric('Hours remaining', f"{total_remaining:.1f}h")
    st.caption(f"Equivalent to {total_banked / standard_day:.1f} days banked.")
    st.caption(f"{total_remaining / standard_day:.1f} days left to take.")

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)
    st.subheader('Log an overtime day')

    col_date, col_hours = st.columns([1, 1])
    entry_date = col_date.date_input('Date', value=date.today(), key='entry_date')
    entry_hours = col_hours.number_input('Hours worked', min_value=0.0, max_value=24.0, step=0.5, format='%.1f', key='entry_hours')

    overtime = entry_hours - standard_day
    if entry_hours > 0:
        if overtime >= 3:
            st.success(f'{overtime:.1f}h overtime — qualifies for annual TOIL pot')
        elif overtime > 0:
            st.info(f'{overtime:.1f}h overtime — below 3h threshold, counts toward monthly flexi only')
        else:
            st.warning('No overtime on this day')

    if st.button('Add to log', key='add_entry'):
        if overtime >= 3:
            entry_date_str = entry_date.strftime('%Y-%m-%d')
            existing_dates = [e['date'] for e in log['entries']]
            if entry_date_str in existing_dates:
                st.error('An entry for this date already exists. Remove it first if you want to update it.')
            else:
                log['entries'].append({
                    'date': entry_date_str,
                    'hours_worked': entry_hours,
                    'overtime_hours': overtime
                })
                log['entries'].sort(key=lambda x: x['date'])
                save_log(log)
                st.rerun()
        else:
            st.error('This day does not meet the 3h overtime threshold for annual TOIL.')

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)
    st.subheader('TOIL hours used')

    hours_used_input = st.number_input('Total TOIL hours used this year', min_value=0.0, step=0.5,
                                        value=float(log['hours_used']), key='hours_used_input')
    if st.button('Update hours used', key='update_used'):
        log['hours_used'] = hours_used_input
        save_log(log)
        st.rerun()

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)
    st.subheader('Log')

    if log['entries']:
        for i, entry in enumerate(log['entries']):
            col_d, col_h, col_o, col_del = st.columns([2, 1, 1, 0.5])
            col_d.write(entry['date'])
            col_h.write(f"{entry['hours_worked']:.1f}h worked")
            col_o.write(f"+{entry['overtime_hours']:.1f}h TOIL")
            if col_del.button('✕', key=f'del_{i}'):
                log['entries'].pop(i)
                save_log(log)
                st.rerun()
    else:
        st.info('No entries yet — log an overtime day above.')

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    if st.button('🗑 Clear all TOIL data', key='clear_log'):
        if 'confirm_clear' not in st.session_state:
            st.session_state.confirm_clear = True

    if st.session_state.get('confirm_clear'):
        st.warning('Are you sure? This will delete all logged entries and reset your hours used.')
        col_yes, col_no = st.columns([1, 1])
        if col_yes.button('Yes, clear everything', key='confirm_yes'):
            save_log({'entries': [], 'hours_used': 0.0, 'standard_day': standard_day})
            st.session_state.confirm_clear = False
            st.rerun()
        if col_no.button('Cancel', key='confirm_no'):
            st.session_state.confirm_clear = False
            st.rerun()

with tab3:
    st.subheader('Hours Today')

    clock_data = load_clock()
    saved_pattern = clock_data.get('work_pattern', '5 days / 40 hours (8h day)')
    pattern_index = 0 if saved_pattern == '5 days / 40 hours (8h day)' else 1
    work_pattern_tab3 = st.radio('Working pattern', ['5 days / 40 hours (8h day)', '4 days / 40 hours (10h day)'], key='pattern_tab3', index=pattern_index)
    target_minutes = 8 * 60 if '8h' in work_pattern_tab3 else 10 * 60
    if work_pattern_tab3 != clock_data.get('work_pattern'):
        clock_data['work_pattern'] = work_pattern_tab3
        save_clock(clock_data)

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    # load clock events from file (persists across refreshes, auto-resets daily)
    clock_data = load_clock()
    events = clock_data['events']
    next_action = 'Clock In' if len(events) == 0 or events[-1]['type'] == 'Clock Out' else 'Clock Out'

    col_time, col_btn = st.columns([2, 1])
    default_time = now_london().strftime('%H:%M')
    event_time_str = col_time.text_input(f'{next_action} time', value=default_time, placeholder='HH:MM', key='event_time')

    if col_btn.button(next_action, key='clock_btn'):
        try:
            parsed = datetime.strptime(event_time_str.strip(), '%H:%M')
            event_time = parsed.time()
            new_minutes = time_to_minutes(event_time)
            if events:
                last_minutes = time_to_minutes(dtime(int(events[-1]['time'].split(':')[0]), int(events[-1]['time'].split(':')[1])))
                if new_minutes <= last_minutes:
                    st.error(f'{next_action} time must be after the previous entry ({events[-1]["time"]}).')
                else:
                    clock_data['events'].append({'type': next_action, 'time': event_time.strftime('%H:%M')})
                    save_clock(clock_data)
                    st.rerun()
            else:
                clock_data['events'].append({'type': next_action, 'time': event_time.strftime('%H:%M')})
                save_clock(clock_data)
                st.rerun()
        except ValueError:
            st.error('Please enter a valid time in HH:MM format, e.g. 08:30')

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    # show current event log
    if events:
        st.markdown('**Today\'s entries**')
        for i, event in enumerate(events):
            col_type, col_t, col_del = st.columns([2, 2, 0.5])
            col_type.write(event['type'])
            col_t.write(event['time'])
            if col_del.button('✕', key=f'del_event_{i}'):
                clock_data['events'].pop(i)
                save_clock(clock_data)
                st.rerun()

        st.markdown(RED_DIVIDER, unsafe_allow_html=True)

        # calculate time worked so far from paired clock in/out events
        minutes_worked = 0
        unpaired_clock_in = None
        last_cin = None
        for event in events:
            t = int(event['time'].split(':')[0]) * 60 + int(event['time'].split(':')[1])
            if event['type'] == 'Clock In':
                last_cin = t
            elif event['type'] == 'Clock Out' and last_cin is not None:
                minutes_worked += t - last_cin
                last_cin = None
        # if last_cin is still set, there's an unpaired clock in
        if last_cin is not None:
            for event in reversed(events):
                if event['type'] == 'Clock In':
                    unpaired_clock_in = event['time']
                    break

        minutes_remaining = target_minutes - minutes_worked
        hours_done = minutes_worked // 60
        mins_done = minutes_worked % 60

        # if currently clocked in, add live elapsed time since last clock in
        # use integer minute arithmetic only to avoid datetime subtraction issues
        if unpaired_clock_in is not None:
            cin_parts = unpaired_clock_in.split(':')
            cin_total = int(cin_parts[0]) * 60 + int(cin_parts[1])
            now_total = now_london().hour * 60 + now_london().minute
            live_elapsed = max(now_total - cin_total, 0)
            live_minutes_worked = minutes_worked + live_elapsed
            live_minutes_remaining = target_minutes - live_minutes_worked
        else:
            live_minutes_worked = minutes_worked
            live_minutes_remaining = minutes_remaining

        hours_done = live_minutes_worked // 60
        mins_done = live_minutes_worked % 60

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric('Hours worked', f'{hours_done}h {mins_done}m')
        col_m2.metric('Target', f'{target_minutes // 60}h')
        col_m3.metric('Remaining', f'{max(live_minutes_remaining, 0) // 60}h {max(live_minutes_remaining, 0) % 60}m')
        
        # auto refresh every 60 seconds while clocked in without losing tab state
        if unpaired_clock_in is not None:
            if 'last_refresh' not in st.session_state:
                st.session_state.last_refresh = now_london().minute
            if now_london().minute != st.session_state.last_refresh:
                st.session_state.last_refresh = now_london().minute
                st.rerun()
            st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

        st.markdown(RED_DIVIDER, unsafe_allow_html=True)

        if unpaired_clock_in is not None:
            # currently clocked in — calculate finish time from now
            cin_parts = unpaired_clock_in.split(':')
            cin_minutes = int(cin_parts[0]) * 60 + int(cin_parts[1])
            finish_minutes = cin_minutes + minutes_remaining
            if minutes_remaining > 0:
                st.success(f'You can clock out for the day at **{minutes_to_time_str(finish_minutes)}**!')
            else:
                overtime_mins = abs(minutes_remaining)
                st.success(f'You\'ve hit your {target_minutes // 60}h target! You\'ve done {overtime_mins // 60}h {overtime_mins % 60}m overtime today.')
        else:
            # currently clocked out — show when they need to clock back in and work remaining time
            if minutes_remaining > 0:
                st.info(f'You have {minutes_remaining // 60}h {minutes_remaining % 60}m left to work today. Clock back in to see your finish time.')
            else:
                overtime_mins = abs(minutes_remaining)
                st.success(f'You\'ve hit your {target_minutes // 60}h target for the day! You have {overtime_mins // 60}h {overtime_mins % 60}m of overtime.')

    else:
        st.info('No entries yet — add your first Clock In time above.')

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    if st.button('Reset today\'s clock', key='reset_clock'):
        save_clock({'date': now_london().strftime('%Y-%m-%d'), 'events': [], 'work_pattern': work_pattern_tab3})
        st.rerun()