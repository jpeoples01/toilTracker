total = 0
hours = []
num_weeks = int(input('How many weeks of work have you done?: '))

for i in range(num_weeks):
    hours.append(float(input('Enter hours worked this week: ')))

def to_minutes(h):
    return int(h) * 60 + round((h % 1) * 100)

total_minutes = sum(to_minutes(h) for h in hours)
print('Hours worked this month:', total_minutes // 60, 'hours and', total_minutes % 60, 'minutes')

if num_weeks == 4:
    leftMinutes = (160 * 60) - total_minutes
    if leftMinutes > 0:
        print(f'You have {leftMinutes // 60} hours & {leftMinutes % 60} minutes left to work to get full pay')
    elif leftMinutes == 0:
        print('You have worked exactly your full hours this month!')
    else:
        overtimeMinutes = abs(leftMinutes)
        print(f'You have {overtimeMinutes // 60} hours & {overtimeMinutes % 60} minutes of overtime this month!')

elif num_weeks == 3:
    leftMinutes = (120 * 60) - total_minutes
    if leftMinutes > 0:
        print(f'You have {leftMinutes // 60} hours & {leftMinutes % 60} minutes left to work to get full pay')
    elif leftMinutes == 0:
        print('You have worked exactly your full hours this month!')
    else:
        overtimeMinutes = abs(leftMinutes)
        print(f'You have worked {overtimeMinutes // 60} hours & {overtimeMinutes % 60} minutes of overtime this month!')

elif num_weeks == 5:
    leftMinutes = (200 * 60) - total_minutes
    if leftMinutes > 0:
        print(f'You have {leftMinutes // 60} hours & {leftMinutes % 60} minutes left to work to get full pay')
    elif leftMinutes == 0:
        print('You have worked exactly your full hours this month!')
    else:
        overtimeMinutes = abs(leftMinutes)
        print(f'You have worked {overtimeMinutes // 60} hours & {overtimeMinutes % 60} minutes of overtime this month!')

else:
    print('Hmm, those number of weeks are not a fit for your current schedule, when Josh is smarter, he will have functionality for this :)')