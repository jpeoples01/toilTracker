import streamlit as st
from datetime import date, timedelta, datetime, time as dtime
from zoneinfo import ZoneInfo
import calendar
import json
import os

# ─────────────────────────────────────────────
#  Utilities
# ─────────────────────────────────────────────

def now_london():
    return datetime.now(ZoneInfo('Europe/London'))

WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER", "local")

# Anchor dataLogs to the directory this file lives in so the path
# resolves identically whether Streamlit is launched from the project
# root, a subdirectory, or via subprocess from conftest.
_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR  = os.path.join(_BASE_DIR, 'dataLogs')
os.makedirs(_DATA_DIR, exist_ok=True)

LOG_FILE   = os.path.join(_DATA_DIR, f"toil_log_{WORKER_ID}.json")
CLOCK_FILE = os.path.join(_DATA_DIR, f"clock_log_{WORKER_ID}.json")

RED_DIVIDER = '<hr style="border:none; border-top: 1px solid #E63946; margin: 1rem 0;">'


def to_minutes(h):
    """Convert HH.MM float to integer minutes. Raises ValueError on bad input."""
    h_str = f"{h:.2f}"
    hours_str, minutes_str = h_str.split(".")
    hours   = int(hours_str)
    minutes = int(minutes_str)
    if minutes >= 60:
        raise ValueError(f"Invalid input: {h} — minutes portion must be < 60 (e.g. 8.30 = 8h 30m)")
    return hours * 60 + minutes


def last_friday_of_month(year, month):
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    offset = (last_day.weekday() - 4) % 7
    return last_day - timedelta(days=offset)


def get_pay_period(year, month):
    payday        = last_friday_of_month(year, month)
    period_end    = payday - timedelta(weeks=1)
    period_end_monday = period_end - timedelta(days=4)
    for num_weeks in [5, 4, 3]:
        start      = period_end_monday - timedelta(weeks=num_weeks - 1)
        prev_month = month - 1 if month > 1 else 12
        prev_year  = year  if month > 1 else year - 1
        prev_payday       = last_friday_of_month(prev_year, prev_month)
        prev_period_end   = prev_payday - timedelta(weeks=1)
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
        if data.get('date') == today:
            return data
    # Auto-reset on a new day; carry forward the saved work pattern if present
    saved_pattern = None
    if os.path.exists(CLOCK_FILE):
        with open(CLOCK_FILE, 'r') as f:
            old = json.load(f)
        saved_pattern = old.get('work_pattern')
    return {
        'date': today,
        'events': [],
        'work_pattern': saved_pattern or '5 days / 40 hours (8h day)',
    }


def save_clock(data):
    with open(CLOCK_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def time_to_minutes(t):
    return t.hour * 60 + t.minute


def minutes_to_time_str(total_minutes):
    total_minutes = total_minutes % (24 * 60)
    h      = total_minutes // 60
    m      = total_minutes % 60
    suffix = 'am' if h < 12 else 'pm'
    display_h = h if h <= 12 else h - 12
    if display_h == 0:
        display_h = 12
    return f'{display_h}:{m:02d}{suffix}'


# ─────────────────────────────────────────────
#  Page setup
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
#  Shared work pattern (replaces 3 separate radios)
#  Stored in clock_data so it persists across sessions.
# ─────────────────────────────────────────────

clock_data = load_clock()

work_pattern = st.radio(
    'Working pattern',
    ['5 days / 40 hours (8h day)', '4 days / 40 hours (10h day)'],
    index=0 if '8h' in clock_data.get('work_pattern', '8h') else 1,
    horizontal=True,
    key='shared_pattern',
)
standard_day   = 8  if '8h' in work_pattern else 10
target_minutes = standard_day * 60   # per-day target for the clock tab

# Persist pattern change immediately
if work_pattern != clock_data.get('work_pattern'):
    clock_data['work_pattern'] = work_pattern
    save_clock(clock_data)

st.markdown(RED_DIVIDER, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Live clock fragment
#
#  @st.fragment(run_every=60) tells Streamlit to re-execute ONLY this
#  function every 60 seconds. The rest of the app — all three tabs and
#  their widgets — is completely unaffected.
#
#  This replaces the old manual approach of checking
#  st.session_state['last_refresh'] != now_london().minute and calling
#  st.rerun(), which triggered a full app rerun every minute, made the
#  UI unstable during tests, and wasted Streamlit server cycles.
# ─────────────────────────────────────────────

@st.fragment(run_every=60)
def _live_metrics(events: list, target_mins: int):
    """Render live worked-time metrics and finish-time message.

    Reruns automatically every 60 seconds so elapsed time stays current
    without touching the rest of the app.
    """
    minutes_worked   = 0
    last_cin         = None
    unpaired_cin_str = None

    for event in events:
        t = int(event['time'].split(':')[0]) * 60 + int(event['time'].split(':')[1])
        if event['type'] == 'Clock In':
            last_cin = t
        elif event['type'] == 'Clock Out' and last_cin is not None:
            minutes_worked += t - last_cin
            last_cin = None

    if last_cin is not None:
        for event in reversed(events):
            if event['type'] == 'Clock In':
                unpaired_cin_str = event['time']
                break

    now_total = now_london().hour * 60 + now_london().minute

    if unpaired_cin_str is not None:
        cin_parts    = unpaired_cin_str.split(':')
        cin_total    = int(cin_parts[0]) * 60 + int(cin_parts[1])
        live_elapsed = max(now_total - cin_total, 0)
    else:
        live_elapsed = 0

    live_minutes_worked    = minutes_worked + live_elapsed
    live_minutes_remaining = target_mins - live_minutes_worked
    hours_done = live_minutes_worked // 60
    mins_done  = live_minutes_worked % 60

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric('Hours worked', f'{hours_done}h {mins_done}m')
    col_m2.metric('Target',       f'{target_mins // 60}h 00m')
    col_m3.metric('Remaining',    f'{max(live_minutes_remaining, 0) // 60}h {max(live_minutes_remaining, 0) % 60}m')

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    if unpaired_cin_str is not None:
        # Finish time is fixed from the moment you clocked in
        cin_parts_fin            = unpaired_cin_str.split(':')
        cin_total_fin            = int(cin_parts_fin[0]) * 60 + int(cin_parts_fin[1])
        minutes_still_needed     = target_mins - minutes_worked
        finish_minutes           = cin_total_fin + minutes_still_needed

        if live_minutes_remaining > 0:
            st.success(f'Finish time: **{minutes_to_time_str(finish_minutes)}**')
        else:
            ot = abs(live_minutes_remaining)
            st.success(
                f"You've hit your {target_mins // 60}h target! "
                f"{ot // 60}h {ot % 60}m overtime so far today."
            )
    else:
        # Clocked out — projected finish updates as time passes
        if live_minutes_remaining > 0:
            projected_finish = now_total + live_minutes_remaining
            st.info(
                f'You have {live_minutes_remaining // 60}h {live_minutes_remaining % 60}m left to work. '
                f'If you clock back in now, you\'ll finish around '
                f'**{minutes_to_time_str(projected_finish)}**.'
            )
        else:
            ot = abs(live_minutes_remaining)
            st.success(
                f"You've hit your {target_mins // 60}h target for the day! "
                f"{ot // 60}h {ot % 60}m of overtime."
            )


# ─────────────────────────────────────────────
#  Tabs
# ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(['TOIL Monthly Tracker', 'TOIL Annual Leave Accruement', 'Hours Today'])

# ═════════════════════════════════════════════
#  TAB 1 — Monthly Tracker
# ═════════════════════════════════════════════

with tab1:
    st.subheader('Pay period')
    st.caption("Enter hours in HH.MM format (e.g. 38.30 = 38h 30m). Minutes must be less than 60.")

    today  = date.today()
    months = [date(today.year, m, 1).strftime('%B %Y') for m in range(1, 13)]
    months += [date(today.year + 1, 1, 1).strftime('%B %Y')]

    default_month_idx  = today.month - 1
    selected_month_str = st.selectbox('Select pay period month', months, index=default_month_idx)

    sel = selected_month_str.split(' ')
    selected_date = date(int(sel[1]), list(calendar.month_name).index(sel[0]), 1)
    period_start, period_end, payday, num_weeks = get_pay_period(selected_date.year, selected_date.month)

    # Pay period info card
    st.markdown(f"""
<div style="display:flex; gap:2rem; margin: 0.5rem 0 0.75rem; padding: 0.75rem 1rem;
     border-left: 3px solid #E63946; background-color: rgba(230,57,70,0.08);
     border-radius: 0 4px 4px 0;">
  <div>
    <div style="font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;opacity:0.6;">Period start</div>
    <div style="font-size:0.85rem;font-weight:500;">{period_start.strftime('%d %b %Y')}</div>
  </div>
  <div>
    <div style="font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;opacity:0.6;">Period end</div>
    <div style="font-size:0.85rem;font-weight:500;">{period_end.strftime('%d %b %Y')}</div>
  </div>
  <div>
    <div style="font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;opacity:0.6;">Payday</div>
    <div style="font-size:0.85rem;font-weight:500;">{payday.strftime('%d %b %Y')}</div>
  </div>
  <div>
    <div style="font-size:0.65rem;letter-spacing:1px;text-transform:uppercase;opacity:0.6;">Weeks</div>
    <div style="font-size:0.85rem;font-weight:500;">{num_weeks}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Weekly hours entry in a bordered container with a header row.
    # Labels appear once at the top instead of repeating on every input.
    hours        = []
    holiday_days = []
    with st.container(border=True):
        h1, h2, h3, h4 = st.columns([1, 2, 2, 1.3])
        h1.markdown('**Week**')
        h2.markdown('**Dates**')
        h3.markdown('**Hours worked**')
        h4.markdown('**Holiday days**')

        for i in range(num_weeks):
            week_start = period_start + timedelta(weeks=i)
            week_end   = week_start + timedelta(days=4)
            r1, r2, r3, r4 = st.columns([1, 2, 2, 1.3])
            r1.markdown(f'**Week {i + 1}**')
            r2.markdown(f'{week_start.strftime("%d %b")} - {week_end.strftime("%d %b")}')
            h  = r3.number_input(
                'Hours worked', min_value=0.0, max_value=168.0, step=0.01,
                format='%.2f', key=f'month_week_{i}',
                label_visibility='collapsed',
            )
            hd = r4.number_input(
                'Holiday days', min_value=0, max_value=7, step=1,
                key=f'month_hols_{i}',
                label_visibility='collapsed',
            )
            hours.append(h)
            holiday_days.append(hd)

    if st.button('Calculate', key='monthly_calc', type='primary', use_container_width=True):
        valid = True
        converted = []
        for i, h in enumerate(hours):
            try:
                converted.append(to_minutes(h))
            except ValueError as e:
                st.error(f'Week {i + 1}: {e}')
                valid = False

        if valid:
            total_holiday_minutes = sum(hd * standard_day * 60 for hd in holiday_days)
            total_worked_minutes  = sum(converted)
            total_minutes         = total_worked_minutes + total_holiday_minutes
            holiday_total_days    = sum(holiday_days)
            target_period_minutes = num_weeks * 40 * 60
            left_minutes          = target_period_minutes - total_minutes

            st.session_state['tab1_result'] = {
                'total_minutes':         total_minutes,
                'holiday_total_days':    holiday_total_days,
                'left_minutes':          left_minutes,
                'target_period_minutes': target_period_minutes,
            }

    # Result displayed in its own container so it visually separates from inputs
    if 'tab1_result' in st.session_state:
        r = st.session_state['tab1_result']
        with st.container(border=True):
            if r['holiday_total_days'] > 0:
                st.info(
                    f"Holiday hours added: {r['holiday_total_days']} day(s) "
                    f"× {standard_day}h = {r['holiday_total_days'] * standard_day}h"
                )

            st.write(
                f"**Total hours this period (worked + holiday):** "
                f"{r['total_minutes'] // 60}h {r['total_minutes'] % 60}m"
            )

            if r['left_minutes'] > 0:
                st.error(
                    f"You have {r['left_minutes'] // 60}h {r['left_minutes'] % 60}m "
                    f"left to work to reach full pay."
                )
            elif r['left_minutes'] == 0:
                st.success('You have worked exactly your full hours this period!')
            else:
                ot = abs(r['left_minutes'])
                st.success(f"You have {ot // 60}h {ot % 60}m of overtime this period!")

# ═════════════════════════════════════════════
#  TAB 2 — Annual TOIL Accruement
# ═════════════════════════════════════════════

with tab2:
    log = load_log()

    # Keep stored standard_day in sync with the shared pattern selector
    if log['standard_day'] != standard_day:
        log['standard_day'] = standard_day
        save_log(log)

    st.caption(
        f'Qualification for Annual TOIL: {standard_day}h work day with 3h+ overtime '
        f'(e.g. {standard_day + 3}h+ worked in a day)'
    )

    total_banked    = sum(e['overtime_hours'] for e in log['entries'])
    total_remaining = total_banked - log['hours_used']

    # ─── Summary metrics ──────────────────────────────────────
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric('Hours banked',    f"{total_banked:.2f}h")
        col2.metric('Hours used',      f"{log['hours_used']:.2f}h")
        col3.metric('Hours remaining', f"{total_remaining:.2f}h")
        st.caption(
            f"Equivalent to {total_banked / standard_day:.2f} days banked  •  "
            f"{total_remaining / standard_day:.2f} days remaining to take"
        )

    # ─── Log an overtime day ──────────────────────────────────
    with st.container(border=True):
        st.subheader('Log an overtime day')

        col_date, col_hours = st.columns([1, 1])
        entry_date  = col_date.date_input('Date', value=date.today(), key='entry_date')
        entry_hours = col_hours.number_input(
            'Hours worked', min_value=0.0, max_value=24.0,
            step=0.25, format='%.2f', key='entry_hours'
        )

        overtime = round(entry_hours - standard_day, 4)
        if entry_hours > 0:
            if overtime >= 3:
                st.success(f'{overtime:.2f}h overtime - qualifies for annual TOIL pot')
            elif overtime > 0:
                st.info(f'{overtime:.2f}h overtime - below 3h threshold, counts toward monthly flexi only')
            elif overtime == 0:
                st.info('Exactly a standard day - no overtime')
            else:
                st.warning('Hours entered are below a standard day')

        if st.button('Add to log', key='add_entry', type='primary'):
            if overtime >= 3:
                entry_date_str = entry_date.strftime('%Y-%m-%d')
                existing_dates = [e['date'] for e in log['entries']]
                if entry_date_str in existing_dates:
                    st.error('An entry for this date already exists. Remove it first if you want to update it.')
                else:
                    log['entries'].append({
                        'date':           entry_date_str,
                        'hours_worked':   entry_hours,
                        'overtime_hours': overtime,
                    })
                    log['entries'].sort(key=lambda x: x['date'])
                    save_log(log)
                    st.rerun()
            else:
                st.error('This day does not meet the 3h overtime threshold for annual TOIL.')

    # ─── Log entries ──────────────────────────────────────────
    with st.container(border=True):
        st.subheader('Log')

        if log['entries']:
            # Header row to label the columns once
            h1, h2, h3, _ = st.columns([2, 2, 2, 0.5])
            h1.caption('Date')
            h2.caption('Hours worked')
            h3.caption('TOIL accrued')

            if 'pending_delete_toil' not in st.session_state:
                st.session_state.pending_delete_toil = None

            for i, entry in enumerate(log['entries']):
                col_d, col_h, col_o, col_del = st.columns([2, 2, 2, 0.5])
                col_d.write(entry['date'])
                col_h.write(f"{entry['hours_worked']:.2f}h worked")
                col_o.write(f"+{entry['overtime_hours']:.2f}h TOIL")

                if st.session_state.pending_delete_toil == i:
                    col_del.markdown('&nbsp;', unsafe_allow_html=True)
                    conf_col1, conf_col2 = st.columns([1, 1])
                    if conf_col1.button('Confirm delete', key=f'confirm_del_{i}', type='primary'):
                        log['entries'].pop(i)
                        save_log(log)
                        st.session_state.pending_delete_toil = None
                        st.rerun()
                    if conf_col2.button('Cancel', key=f'cancel_del_{i}'):
                        st.session_state.pending_delete_toil = None
                        st.rerun()
                else:
                    if col_del.button('✕', key=f'del_{i}'):
                        st.session_state.pending_delete_toil = i
                        st.rerun()
        else:
            st.info('No entries yet - log an overtime day above.')

    # ─── TOIL hours used ──────────────────────────────────────
    with st.container(border=True):
        st.subheader('TOIL hours used')

        col_input, col_button = st.columns([3, 1])
        hours_used_input = col_input.number_input(
            'Total TOIL hours used this year', min_value=0.0, step=0.25,
            value=float(log['hours_used']), key='hours_used_input'
        )
        # Spacer to align the button vertically with the input
        col_button.write('')
        col_button.write('')
        if col_button.button('Update hours used', key='update_used', use_container_width=True):
            log['hours_used'] = hours_used_input
            save_log(log)
            st.rerun()

    # ─── Destructive action, kept visually separate ───────────
    st.write('')   # vertical breathing room
    if st.button('🗑 Clear all TOIL data', key='clear_log'):
        st.session_state.confirm_clear = True

    if st.session_state.get('confirm_clear'):
        st.warning('Are you sure? This will delete all logged entries and reset your hours used.')
        col_yes, col_no = st.columns([1, 1])
        if col_yes.button('Yes, clear everything', key='confirm_yes', type='primary'):
            save_log({'entries': [], 'hours_used': 0.0, 'standard_day': standard_day})
            st.session_state.confirm_clear = False
            st.rerun()
        if col_no.button('Cancel', key='confirm_no'):
            st.session_state.confirm_clear = False
            st.rerun()

# ═════════════════════════════════════════════
#  TAB 3 — Hours Today
# ═════════════════════════════════════════════

with tab3:
    st.subheader('Hours Today')

    # Single load; already done above for pattern detection — reload for freshest events
    clock_data = load_clock()
    events     = clock_data['events']

    next_action = 'Clock In' if (not events or events[-1]['type'] == 'Clock Out') else 'Clock Out'

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    col_time, col_btn = st.columns([2, 1])
    default_time   = now_london().strftime('%H:%M')
    event_time_str = col_time.text_input(
        f'{next_action} time', value=default_time,
        placeholder='HH:MM', key='event_time'
    )

    if col_btn.button(next_action, key='clock_btn'):
        try:
            parsed     = datetime.strptime(event_time_str.strip(), '%H:%M')
            event_time = parsed.time()
            new_minutes = time_to_minutes(event_time)

            if events:
                last_t = events[-1]['time']
                last_minutes = int(last_t.split(':')[0]) * 60 + int(last_t.split(':')[1])
                if new_minutes <= last_minutes:
                    st.error(f'{next_action} time must be after the previous entry ({last_t}).')
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

    if events:
        st.markdown("**Today's entries**")
        for i, event in enumerate(events):
            col_type, col_t, col_del = st.columns([2, 2, 0.5])
            col_type.write(event['type'])
            col_t.write(event['time'])
            if col_del.button('✕', key=f'del_event_{i}'):
                clock_data['events'].pop(i)
                save_clock(clock_data)
                st.rerun()

        st.markdown(RED_DIVIDER, unsafe_allow_html=True)

        # Fragment handles all live calculations and auto-reruns every 60s.
        # No session_state minute-tracking or manual st.rerun() needed.
        _live_metrics(events, target_minutes)

    else:
        st.info("No entries yet - add your first Clock In time above.")

    st.markdown(RED_DIVIDER, unsafe_allow_html=True)

    if st.button("Reset today's clock", key='reset_clock'):
        save_clock({
            'date':         now_london().strftime('%Y-%m-%d'),
            'events':       [],
            'work_pattern': work_pattern,
        })
        st.rerun()