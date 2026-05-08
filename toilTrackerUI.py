import streamlit as st
 
st.title('TOIL Tracker')
 
def to_minutes(h):
    return int(h) * 60 + round((h % 1) * 100)
 
num_weeks = st.selectbox('How many weeks of work have you done?', [3, 4, 5])
 
hours = []
for i in range(num_weeks):
    h = st.number_input(f'Hours worked in week {i + 1}', min_value=0.0, max_value=168.0, step=0.01, format='%.2f')
    hours.append(h)
 
if st.button('Calculate'):
    total_minutes = sum(to_minutes(h) for h in hours)
    st.write(f'**Hours worked this month:** {total_minutes // 60} hours and {total_minutes % 60} minutes')
 
    targets = {3: 120, 4: 160, 5: 200}
    leftMinutes = (targets[num_weeks] * 60) - total_minutes
 
    if leftMinutes > 0:
        st.error(f'You have {leftMinutes // 60} hours & {leftMinutes % 60} minutes left to work to get full pay')
    elif leftMinutes == 0:
        st.success('You have worked exactly your full hours this month!')
    else:
        overtimeMinutes = abs(leftMinutes)
        st.success(f'You have worked {overtimeMinutes // 60} hours & {overtimeMinutes % 60} minutes of overtime this month!')