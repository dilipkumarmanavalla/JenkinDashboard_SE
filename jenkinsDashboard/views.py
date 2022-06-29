from django.shortcuts import render
from django.views.generic import View
from rest_framework.decorators import api_view, renderer_classes
from django.http import HttpResponse
import jenkins
import datetime
import math
import random
import json

server = jenkins.Jenkins(
    "https://testmap-deploy.adfdata.net",
    username="manavalladilipkumar",
    password="Dilip@2129",
)


@api_view(('GET',))
def get_console_output(req):
    req_data=req.GET['data'].split(':::')
    data=str(server.get_build_console_output(req_data[0], int(req_data[1]))).split('\n')
    data={'console_output':data,'build_no':req_data[1]}
    return HttpResponse(json.dumps({'data': data,'success':True}), content_type="application/json")

def get_builds_information(*a,**b):
    lst = []
    build_table=[]
    branch="assetmanagement/UT_90_New_TestCases"
    info = server.get_job_info(branch)
    builds = info["builds"]
    s = []

    suc, fai, uns, abo = (0, 0, 0, 0)
    build_runners=[]
    for i in range(0,len(builds)):
        lst.append(builds[i]["number"])
        build_info = server.get_build_info(
            branch, builds[i]["number"]
        )
        build_table.append(build_info)
        if build_info["result"] == "FAILURE":
            fai=fai+1
        elif build_info["result"] == "SUCCESS":
            suc=suc+1
        elif build_info["result"] == "UNSTABLE":
            uns= uns + 1
        else:
            abo=abo+1
        if 'causes' in build_info['actions'][0].keys():
            if 'userName' in build_info['actions'][0]['causes'][0].keys():
                build_runners.append(build_info['actions'][0]['causes'][0]['userName'])
                continue
        build_runners.append('Auto Build')
    build_runners_data=[]
    for i in list(set(build_runners)):
        letters = '0123456789ABCDEF'
        color = '#'
        for j in range(0, 6):
            color = color + letters[math.floor(random.random() * 16)]
        build_runners_data.append([i.capitalize(), build_runners.count(i), color])
    build_runners_data=sorted(build_runners_data, key = lambda i: i[1],reverse=True)
    build_runners_data.insert(0,['Task','Build Runner Chart',{ 'role': "style" }])
    data={
        'build_table':build_table,
        'build_status_pie_data':[suc,fai,uns,abo],
        'build_numbers':lst,
        'build_runners_bar_data':build_runners_data,
        'branch':branch
    }
    return data




def builds_table(data,branch):
    tim_duration={}
    for i in range(0, len(data)):
        tim=round((data[i]["duration"]/60)/60,1)

        tim_duration[data[i]['number']]=tim
        timestamp=int(str(data[i]['timestamp'])[:10])
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        time=timestamp.strftime('%Y-%m-%d %H:%M')
        commit=data[i]["description"] if data[i]["description"]!=None else 'N/A'

        data[i] = {
            "s_no": i + 1,
            "build_no": str(data[i]["id"]),
            "branch": data[i]["fullDisplayName"],
            "path":str(branch),
            "result": data[i]["result"],
            "description": commit,
            "date":time,
            "duration":str(round(tim/60,1))+'H'if tim>60 else str(tim)+'M'
        }
    print(print(tim_duration,'TimDuration'))
    return data


class HomeView(View):
    def get(self, request, *args, **kwargs):
        data=get_builds_information()
        build_table_data=builds_table(data['build_table'],data['branch'])
        labels, chart_data, build_runner = data['build_numbers'],data['build_status_pie_data'],data["build_runners_bar_data"]

        chart_label = "success-failure rate "
        temp = ['Success', 'Failure', 'Unstable', 'Abort']
        pie_data = list(map(lambda x: [temp[chart_data.index(x)], x], chart_data))
        temp = ['green', 'red', 'orange', 'blue']
        pie_data.insert(0, ['Task', 'Build Status Chart'])

        builds=list(map(lambda x:{'des':x[0],'count': x[1],'colour': temp[pie_data.index(x)-1]},pie_data[1:]))
        builds.insert(0,{'des':'Jobs','count': sum(i[1] for i in pie_data[1:]),'colour':'grey'})

        data = {
            "labels": labels,
            "chartLabel": chart_label,
            "chartdata": chart_data,
            "pie": pie_data,
            "bar": build_runner,
            "bg_colours": temp,
        }
        return render(request, "index.html", {"builds_table": build_table_data,"data":json.dumps(data),"builds":builds})
