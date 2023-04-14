# Importing necessary packages
import pandas as pd
import numpy as np
import itertools
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import Select, CheckboxGroup, ColumnDataSource, Range1d, Legend
from bokeh.plotting import figure, show
from bokeh.palettes import Category20c as palette

# group by function
def group_data(data, group):
    if group == "None":
        groupedData = data.groupby(["year"]).sum().reset_index()
    else:
        groupedData = data.groupby([group, "year"]).sum().reset_index()
    groupedData["suicide_rate"] = (groupedData["suicides_no"]/groupedData["population"]) * 10000 # creating the suicide rate variable
    groupedData["suicide_rate"].replace([np.inf, -np.inf], 0, inplace= True) # replacing the infinity values
    return groupedData

# reading in the data
hfi = pd.read_csv("hfi_cc_2021.csv")
who = pd.read_csv("who_suicide_statistics.csv")

#############################################################################################################
##                          VISUALIZATION 1 - INTERACTIVE TIME SERIES
#############################################################################################################

# cleaning data
who.fillna(0, inplace = True)
who["suicide_rate"] = (who["suicides_no"] / who["population"]) * 10000
who["suicide_rate"].replace([np.inf, -np.inf], 0, inplace= True)

# possible variables
group_var_options = ["country", "sex", "age", "None"]
years = [str(x) for x in sorted(who.year.unique())]
levels = ["None"]
start = group_data(who, "None")
xs = [start["year"]]
ys = [start["suicide_rate"]]

# defining colors
color_choices = list(palette[20])
print(color_choices)
while len(color_choices) > len(levels):
    color_choices.pop()


#defining ColumnDataSource - What manages the changing parts of the visualization
source = ColumnDataSource(data={'xs': xs, 'ys': ys, 'color_choices': color_choices, 'legend_group': ["suicide_rate"], 'labels': levels})

# Create Input controls
min_year = Select(title = "Starting Year", options = years, value = "1979")
max_year = Select(title = "Ending Year", options = years, value = "2016")
group_var = Select(title = "Grouping Variable", options = sorted(group_var_options), value= "None")
group_levels = CheckboxGroup(labels = levels)

# creating the plot
p = figure(height = 400, width = 700, title = "", toolbar_location = None, sizing_mode = "scale_both")
p.xaxis.axis_label = "Years"
p.yaxis.axis_label = "Suicide Rate (Suicides / 10,000 people)"
p.x_range = Range1d(1979, 2016, bounds = "auto")
p.y_range = Range1d(0, 4, bounds = "auto")

p.multi_line(xs='xs', ys = 'ys', line_color = 'color_choices', legend = 'labels', source = source)
p.legend.location = "top_right"

# function to select the data that will be used by the visualization. Overall this just groups the data into the different attribute levels
def select_data():
    global levels

    group_val = group_var.value
    start_year = int(min_year.value)
    end_year = int(max_year.value)
    levels_choice = [group_levels.labels[i] for i in group_levels.active]
    
    df = group_data(who, group_val)
    
    if group_val != "None":
        levels = [str(x) for x in sorted(df[group_val].unique())]
        group_levels.labels = levels
        selected = df[
            (df["year"] >= start_year) &
            (df["year"] <= end_year) &
            (df[group_val].isin(levels_choice))
        ]
    else:
        group_levels.labels = ["None"]
        selected = df[
            (df["year"] >= start_year) &
            (df["year"] <= end_year)
        ]

    return selected

# resets the active attribute boxes checked when a new grouping variable is chosen
def reset_active():
    group_levels.active = [0]

# function that updates the graph when changes to the inputs happen
def update():
    global xs
    global ys
    global color_choices

    df = select_data() # selects the new data
    print(df)
    ys = []
    xs = []

    # makes changes depending on if a grouping variable is called
    if group_var.value != "None":
        labels = df[group_var.value].unique()
        p.title.text = "International Suicide Rates Grouped By {} ({} - {})".format(group_var.value, min_year.value, max_year.value)
        
        for label in labels:
            xs.append(df.loc[df[group_var.value] == label, "year"])
            ys.append(df.loc[df[group_var.value] == label, "suicide_rate"])

    else:
        ys = [df["suicide_rate"]]
        xs = [df["year"]]
        labels = ["None"]
        p.title.text = "International Suicide Rates Between {} and {}".format(min_year.value, max_year.value)
    
    # chooses the colors that will be used. Takes the full pallette into a list and then pops the end off
    # does this until the length of the list matches the number of attributes chosen
    color_choices = list(palette[20])
    while len(color_choices) > len(labels):
        color_choices.pop()
    
    print(color_choices)
    print(labels)

    source.data = {'xs': xs, 'ys': ys, 'color_choices': color_choices, 'labels': labels }

# updating the controls
controls = [min_year, max_year, group_var, group_levels]
for control in controls:
    if control == group_levels: # updates if the attribute levels are changed
        control.on_change('active', lambda attrname, old, new: update())
    elif control == group_var: # updates if the grouping variable is changed
        control.on_change('value', lambda attrname, old, new: update())
        control.on_change('value', lambda attrname, old, new: reset_active()) # resets the active attribute checkboxes to fix bug
    else: # updates for everythig else
        control.on_change('value', lambda attrname, old, new: update())

# setting the inputs for the figure
inputs = column(min_year, max_year, group_var, group_levels)

# settings for the output 
l = column(row(inputs, p), sizing_mode = "scale_both")

# intial updating and running
update()
curdoc().add_root(l)
curdoc().title = "International Suicide Rates"

###########################################################################
######### TO SHOW THIS ACTIVE VISUALIZATION
### RUN THE DATA
### TYPE "python -m bokeh serve --show project_code.py" into the terminal
### project_code.py -> name of program. If changed you need to change this
###########################################################################

#############################################################################################################
##                          VISUALIZATION 1 - SCATTER PLOT
#############################################################################################################
p2 = figure(height = 300, width = 600, title = "International Suicide Rate vs. Human Freedom Index", toolbar_location = None, sizing_mode = "scale_both")

# grouping the data by country and year to get suicide rate 
who2 = who.groupby(["country", "year"]).sum().reset_index()
who2["suicide_rate"] = (who2["suicides_no"]/who2["population"]) * 10000
who2["suicide_rate"].replace([np.inf, -np.inf], 0, inplace= True)

# merging the data
combined = who2.merge(hfi[["year", "countries", "hf_score"]], how = "left", left_on = ["country", "year"], right_on = ["countries", "year"])
combined = combined[combined['year'] == 2010]
combined = combined.dropna(axis = 0)

# Making the scatter plot
p2.scatter(y = combined['suicide_rate'], x = combined['hf_score'])
p2.x_range = Range1d(0, 10, bounds = "auto")
p2.y_range = Range1d(0, 4, bounds = "auto")
p2.xaxis.axis_label = "Human Freedom Index Score (0 - 10)"
p2.yaxis.axis_label = "Suicide Rate (Suicides / 10,000 people)"

#making the correlation line
corr = np.polyfit(combined["hf_score"], combined["suicide_rate"], 1, full = True)
slope = corr[0][0]
intercept = corr[0][1]
line_best_fit = []
for i in combined["hf_score"]:
    line_best_fit.append(slope*i + intercept)

p2.line(x = combined["hf_score"], y = line_best_fit, color = "red")


# showing the graph
show(p2)

# testing
print(combined)


#################################################################################################
####                                        REFERENCES
#################################################################################################
# Bokeh documentation -> https://docs.bokeh.org/en/latest/
# Bokeh tutorial -> https://www.geeksforgeeks.org/python-bokeh-plotting-multiple-lines-on-a-graph/
# Chosing the color palettes -> https://docs.bokeh.org/en/latest/docs/reference/palettes.html
# Examples materials used for learning -> https://docs.bokeh.org/en/latest/docs/gallery.html
