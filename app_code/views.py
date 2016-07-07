from app_code import app
from flask import render_template
from flask import request

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

import mpld3
from mpld3 import plugins, fig_to_html


# class PointLabelTooltip(PluginBase):
#     """A Plugin to enable a tooltip: text which hovers over points.

#     Parameters
#     ----------
#     points : matplotlib Collection or Line2D object
#         The figure element to apply the tooltip to
#     labels : array or None
#         If supplied, specify the labels for each point in points.  If not
#         supplied, the (x, y) values will be used.
#     hoffset, voffset : integer
#         The number of pixels to offset the tooltip text.  Default is
#         hoffset = 0, voffset = 10

#     Examples
#     --------
#     >>> import matplotlib.pyplot as plt
#     >>> from mpld3 import fig_to_html, plugins
#     >>> fig, ax = plt.subplots()
#     >>> points = ax.plot(range(10), 'o')
#     >>> plugins.connect(fig, PointLabelTooltip(points[0]))
#     >>> fig_to_html(fig)
#     """
#     def __init__(self, points, labels=None,
#                  hoffset=0, voffset=10, location="mouse"):
#         if location not in ["bottom left", "top left", "bottom right",
#                             "top right", "mouse"]:
#             raise ValueError("invalid location: {0}".format(location))
#         if isinstance(points, matplotlib.lines.Line2D):
#             suffix = "pts"
#         else:
#             suffix = None
#         self.dict_ = {"type": "tooltip",
#                       "id": get_id(points, suffix),
#                       "labels": labels,
#                       "hoffset": hoffset,
#                       "voffset": voffset,
#                       "location": location}


output=None

@app.route('/')
@app.route('/index')
def index():
   return render_template("index.html")

@app.route('/results') 
def results():
    #Amazing code for interactive matplotlib:
    #http://mpld3.github.io/examples/html_tooltips.
#these files bellow need to be first unzipped. Zipped format to avoit Githubs file size restrictions
    ClustLoc = pd.read_csv('app_code/data/ClusterCoords.txt', sep="\t") #The tree coords and the cluster they belong
    t_num = pd.read_csv('app_code/data/Numbers_tab.csv')  #Number of trees
    t_surv = pd.read_csv('app_code/data/Survival_tab.csv')  #Probability of survival
    t_name = pd.read_csv('app_code/data/Tree_names_tab.csv')  #Match of latin and common names

#Geocoding user input
    address =request.args.get('address')
    address = address.lower()

#If there is no address input,or they just entered New York then return results for entire NY
    
    if address=="ny" or address=="new york" or address=="nyc" or address=="new york city" or len(address)==0:
        #Select and organize data
    #This is the numbers of each tree in New York
        num = t_num.drop('Cluster', 1)
        num = num.sum(axis=0)
        
    #Before I convert numbers to frequencies, get the total nuber of trees in New York
        num_trees = num.sum()
        
    #now convert each species to frequences
        num = num.divide(float(num_trees))*100

    #This is the probability of survival of each tree in New York
        temp_num = t_num.drop('Cluster', 1)
        temp_surv = t_surv.drop('Cluster', 1)

    #this is the calculation the species-wise survivors for the entire NYC
        temp_surv = pd.DataFrame(temp_num.values*temp_surv.values, columns=temp_num.columns, index=temp_num.index)
        temp_surv = temp_surv.sum(axis=0)

    #Now convert the absolute survivors to frequencies
        temp_num = temp_num.sum(axis=0)

        surv = temp_surv.divide(temp_num)*100

    #Create the New York-wise table
        frames = [surv, num]
        temp = pd.concat(frames,axis=1,keys=['surv', 'num'])
        #temp = temp.reset_index(level=1, drop=True)
        temp = temp.sort(columns='surv',ascending=False)

    #Finally, switch species for common names
        a = list(t_name['Common'])
        b = list(t_name['Latin'])
        c = list(temp.index.values)

        common_names = []
        for i in range(len(a)):
            for j in range(len(c)):
                if c[j]==b[i]:
                    common_names.append(a[i])

        adrs = "New York, NY"
    else:
        if address.find("ny")<0:
            address = address + " NY" 
#URL encoding
        service_url = "https://maps.googleapis.com/maps/api/geocode/json?"

    #if len(address)<1: print "Please enter an address"

    

    #These are urllib commands
    #url = service_url + urllib.urlencode({'address':address, 'key':"###################################"})
    # uh = urllib.urlopen(url)
    # data = uh.read()
    #js = json.loads(str(data))

    #These are requests commands
        parameters = {'address':address, 'key':"#############################"}

        r = requests.get(service_url, params=parameters)
        js = r.json()

        lat = js['results'][0]['geometry']['location']['lat']
        lon = js['results'][0]['geometry']['location']['lng']
        adrs = js['results'][0]['formatted_address']
        q = tuple([lat, lon])

 #Identify cluster
        ClustLoc['dLat'] = (ClustLoc.latitude  - q[0])**2.
        ClustLoc['dLon'] = (ClustLoc.longitude - q[1])**2.
        ClustLoc['dist'] = (ClustLoc.dLat + ClustLoc.dLon)**0.5   
        i = ClustLoc['dist'].idxmin(axis='index') #the index of the minimum distance tree
        cluster = ClustLoc['Cluster'].ix[i] #its number

    #If the closest tree is more than 1.11Km away, then we have no data!
 #   d =  ClustLoc['dist'].min(axis='index')
 #   if d>=0.01:
 #       print "Sorry there is no information for the location you chose"

 #Select and organize data
    #This is the numbers of each tree in the selected cluster
        num = t_num[t_num['Cluster']=="Cluster"+str(cluster)]
        num = num.drop('Cluster', 1)
        num = num.dropna(axis='columns',)

    #Before I convert numbers to frequencies, get the total nuber of trees in the cluster
        num_trees = str(num.sum(axis=1))
        num_trees = float(num_trees.split()[1])
        num_trees = int(num_trees)

    #now convert each species to frequences
        num = num.divide(float(num.sum(axis=1)))*100

    #This is the probability of survival of each tree in the selected cluster
        surv = t_surv[t_surv['Cluster']=="Cluster"+str(cluster)]
        surv = surv.drop('Cluster', 1)
        surv = surv.dropna(axis=1)*100

        frames = [surv, num]
        temp = pd.concat(frames,keys=['surv', 'num'])
        temp = temp.reset_index(level=1, drop=True)
        temp = temp.transpose()
        temp = temp.sort(columns='surv',ascending=False)

        #Finally, switch species for common names
        a = list(t_name['Common'])
        b = list(t_name['Latin'])
        c = list(temp.index.values)

        common_names = []
        for i in range(len(a)):
            for j in range(len(c)):
                if c[j]==b[i]:
                    common_names.append(a[i])

#Pick top three values
    maximums = list(temp['surv'][0:3].values)

    first_val = "%.2f" % maximums[0]+'%'
    second_val = "%.2f" % maximums[1]+'%'
    third_val = "%.2f" % maximums[2]+'%'

    first_sp = common_names[0]
    second_sp = common_names[1]
    third_sp = common_names[2]               

#Make plot
    fig, ax = plt.subplots(subplot_kw=dict(axisbg='#FFFFFF'))

    scatter = ax.scatter(temp['surv'],
                          temp['num'],
                          c=temp['surv'],
                          cmap ='Greens',
                          s= 100,
                          alpha=1)

    ax.set_title("Total number of trees considered: "+ str(num_trees), size=20, color='darkgreen', fontweight='heavy')

    ax.set_xlabel('% Likelihood of survival past 10 years', fontsize=18)
    ax.set_ylabel('% of all trees considered', fontsize=18)

    labels = common_names

    tooltip = mpld3.plugins.PointHTMLTooltip(scatter, labels=labels)
    mpld3.plugins.connect(fig, tooltip)  
    fig_html = mpld3.fig_to_html(fig)

    return render_template("results.html",address=adrs, first_val=first_val,second_val=second_val,third_val=third_val,first_sp=first_sp,second_sp=second_sp,third_sp=third_sp, plot=fig_html) 
    
    
