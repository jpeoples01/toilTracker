import streamlit as st
from datetime import date, timedelta
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
LOG_FILE = 'toil_log.json'

def to_minutes(h):
    return int(h) * 60 + round((h % 1) * 100)

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

tab1, tab2 = st.tabs(['TOIL Monthly Tracker', 'TOIL Annual Leave Accruement'])

with tab1:
    work_pattern_tab1 = st.radio('Working pattern', ['5 days / 40 hours', '4 days / 40 hours'], key='pattern_tab1')

    if work_pattern_tab1 == '5 days / 40 hours':
        standard_day_tab1 = 8
    else:
        standard_day_tab1 = 10

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)
    st.subheader('Pay period')

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

    # summary metrics
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