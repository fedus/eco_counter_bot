import pandas
import os

import plotly.express as px

from arrow import Arrow
from datetime import datetime

from eco_counter_bot.utils import format_number_lb
from eco_counter_bot.models import CounterData, DataPoint

def customize_legend_name(fig, new_names):
    for i, new_name in enumerate(new_names):
        fig.data[i].name = new_name

def get_count_for(day: datetime or Arrow, count_data: CounterData) -> int or None:
    return next(filter(lambda data_point: data_point["date"].day == day.date().day and data_point["date"].month == day.date().month, count_data), DataPoint(date=day, count=None))["count"]

def generate_yearly_plot(previous_year_cd: CounterData, current_year_cd: CounterData):
    previous_year_simple = previous_year_cd[0]["date"].year
    current_year_simple = current_year_cd[0]["date"].year

    current_year_start = current_year_cd[0]["date"].replace(month=1, day=1)
    current_year_end = current_year_start.replace(month=12, day=31)

    cutoff_day = current_year_cd[-1]["date"]
    cutoff_day_index =  cutoff_day.timetuple().tm_yday - 1

    all_current_year_days = list(Arrow.range("day", Arrow.fromdate(current_year_start), Arrow.fromdate(current_year_end)))

    previous_year_values = [get_count_for(day, previous_year_cd) for day in all_current_year_days]
    current_year_values = [get_count_for(day, current_year_cd) for day in all_current_year_days]

    data = {
        'date': all_current_year_days,
        'curr': current_year_values,
        'prev': previous_year_values
    }

    print(data)

    df = pandas.DataFrame(data)

    fig = px.line(
        df,
        x="date",
        y=["curr", "prev"],
        title=f"<b>Luxembourg-City bike counts</b><br>{current_year_simple} vs {previous_year_simple}<br><i>{cutoff_day.strftime('%d %B %Y')}</i>",
        labels={ "date": "Date", "curr": current_year_simple, "prev": previous_year_simple, "variable": "Year" },
        width=800,
        height=600,
    )

    fig.update_traces(line=dict(width=4))

    customize_legend_name(fig, [current_year_simple, previous_year_simple])

    fig.add_scatter(x = [fig.data[1].x[cutoff_day_index]], y = [fig.data[1].y[cutoff_day_index]],
                        mode = 'markers + text',
                        marker = {'color':'red', 'size':14},
                        showlegend = False,
                        text = f"<b>{format_number_lb(int(fig.data[1].y[cutoff_day_index]))}</b>",
                        textposition='middle right',
                        textfont = { 'color': 'red' })

    fig.add_scatter(x = [fig.data[0].x[cutoff_day_index]], y = [fig.data[0].y[cutoff_day_index]],
                        mode = 'markers + text',
                        marker = {'color':'blue', 'size':14},
                        showlegend = False,
                        text = f"<b>{format_number_lb(int(fig.data[0].y[cutoff_day_index])):}</b>",
                        textposition='top left',
                        textfont = { 'color': 'blue' })

    fig.add_hline(y=fig.data[1].y[-1], line_dash="dot", line_color="red",
        annotation_text=f"{previous_year_simple} total: <b>{format_number_lb(int(fig.data[1].y[-1]))}</b>", 
        annotation_position="top right",
        annotation_font_color="red")

    fig.update_yaxes(title_text="<b>Bike</b> counts", secondary_y=False)
    fig.update_yaxes(rangemode="nonnegative")

    fig.update_xaxes(
        dtick="M1",
        tickformat="%b")

    fig.add_layout_image(
        dict(
            source="https://raw.githubusercontent.com/fedus/eco_counter_bot/main/res/header.png",
            xref="paper", yref="paper",
            x=1, y=1.025,
            sizex=0.5, sizey=0.5,
            xanchor="right", yanchor="bottom"
        )
    )

    fig.add_layout_image(
        dict(
            source="https://raw.githubusercontent.com/fedus/eco_counter_bot/main/res/footer.png",
            xref="paper", yref="paper",
            x=1, y=0,
            sizex=0.5, sizey=0.5,
            xanchor="right", yanchor="bottom"
        )
    )

    fig.update_layout(template='plotly_white')

    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    fig.write_image("tmp/daily_fig.png")
