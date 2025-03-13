def calculate_total_time(time_array):
    total_minutes = 0

    for time_str in time_array:
        hours, minutes = map(int, time_str.split(':'))
        total_minutes += hours * 60 + minutes

    result_hours = total_minutes // 60
    result_minutes = total_minutes % 60

    return f"{result_hours}:{result_minutes:02d}"
